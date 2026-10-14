package example.placeholder.common

import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.float
import kotlinx.serialization.json.int
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.longOrNull
import org.jsoup.Jsoup
import java.net.URI
import java.text.Normalizer
import java.util.Locale

/** This is extension-owned policy, not a rule injected into Nyanime. */
class SiteAddress(
    base: String,
) {
    private val root = URI(base)

    init {
        require(root.host != null && root.userInfo == null && root.query == null && root.fragment == null)
        require(root.scheme == "https" || root.scheme == "http" && root.host in setOf("localhost", "127.0.0.1"))
        require(root.path.endsWith('/')) { "Website base URL must end with /" }
    }

    fun url(reference: String): String {
        require(reference.isNotBlank() && reference.length <= 2048 && '\\' !in reference)
        require(!Regex("(?i)%(?:2e|2f|5c)").containsMatchIn(reference)) { "Encoded path traversal rejected" }
        val target = root.resolve(reference).normalize()
        require(target.scheme == root.scheme && target.host == root.host && target.port == root.port)
        require(target.userInfo == null && target.query == null && target.fragment == null)
        require(target.path.startsWith(root.path)) { "Link leaves this extension's website area" }
        return target.toASCIIString()
    }

    fun reference(url: String): String = URI(this.url(url)).path
}

data class Entry(
    val id: String,
    val medium: String,
    val title: String,
    val url: String,
    val cover: String,
    val banner: String,
    val genre: String,
    val description: String,
    val updatedAt: Long,
    val format: String = "Animation",
)

data class Query(
    val text: String = "",
    val genre: String = "All",
    val order: String = "Popular",
    val date: String = "",
    val format: String = "All",
)

data class EntryPage(
    val entries: List<Entry>,
    val hasNext: Boolean,
)

data class Part(
    val url: String,
    val name: String,
    val number: Float,
    val publishedAt: Long,
)

data class EntryDetails(
    val entry: Entry,
    val parts: List<Part>,
)

data class Stream(
    val url: String,
    val label: String,
    val resolution: Int,
    val subtitles: List<Pair<String, String>>,
)

object SiteParser {
    private val json = Json { ignoreUnknownKeys = true }

    private fun JsonObject.text(key: String) = requireNotNull(this[key]?.jsonPrimitive?.contentOrNull) { "Missing field: $key" }

    fun objectFrom(body: String): JsonObject = json.parseToJsonElement(body).jsonObject

    fun dataFromHtml(body: String): JsonObject {
        val element =
            Jsoup.parse(body).selectFirst("script#entry-data[type=application/json]")
                ?: error("Page structure changed: entry data is missing")
        return objectFrom(element.data())
    }

    fun entry(
        value: JsonObject,
        address: SiteAddress,
    ) = Entry(
        value.text("id"),
        value.text("medium"),
        value.text("title"),
        address.reference(value.text("url")),
        address.url(value.text("cover")),
        address.url(value.text("banner")),
        value.text("genre"),
        value.text("description"),
        value["publishedAt"]?.jsonPrimitive?.longOrNull ?: 0L,
        value["format"]?.jsonPrimitive?.contentOrNull ?: "Animation",
    )

    fun catalogue(
        body: String,
        address: SiteAddress,
    ): List<Entry> {
        val value = objectFrom(body)
        require(value["schema"]?.jsonPrimitive?.int == 1) { "Unsupported catalogue schema" }
        val entries = value["entries"]!!.jsonArray.map { entry(it.jsonObject, address) }
        require(entries.size <= 500 && entries.map { it.id }.distinct().size == entries.size)
        return entries
    }

    fun details(
        body: String,
        address: SiteAddress,
    ): EntryDetails {
        val root = dataFromHtml(body)
        val entry = entry(root["entry"]!!.jsonObject, address)
        val parts =
            root["parts"]!!.jsonArray.map { item ->
                item.jsonObject.let {
                    Part(
                        address.reference(it.text("url")),
                        it.text("name"),
                        it["number"]!!.jsonPrimitive.float,
                        it["publishedAt"]?.jsonPrimitive?.longOrNull ?: 0L,
                    )
                }
            }
        require(parts.map { it.url }.distinct().size == parts.size && parts.all { it.number.isFinite() && it.number >= 0 })
        // Source list convention: newest first. Nyanime owns the user's chosen display order.
        return EntryDetails(entry, parts.sortedByDescending { it.number })
    }

    fun streams(
        body: String,
        address: SiteAddress,
    ): List<Stream> {
        val doc = Jsoup.parse(body)
        val subtitles =
            doc.select("video track[kind=subtitles][src]").map {
                address.url(it.attr("src")) to it.attr("srclang").ifBlank { "en" }
            }
        return doc
            .select("video source[src]")
            .map {
                Stream(
                    address.url(it.attr("src")),
                    it.attr("data-label").ifBlank { "Demo" },
                    it.attr("data-height").toIntOrNull() ?: 0,
                    subtitles,
                )
            }.also { require(it.isNotEmpty()) { "No supported video was published on this page" } }
    }

    fun pages(
        body: String,
        address: SiteAddress,
    ): List<String> =
        Jsoup
            .parse(body)
            .select("main.reader img[data-page][src]")
            .map { address.url(it.attr("src")) }
            .also { require(it.isNotEmpty()) { "This chapter has no published pages" } }

    fun page(
        entries: List<Entry>,
        medium: String,
        page: Int,
        query: Query,
        pageSize: Int = 3,
    ): EntryPage {
        require(page in 1..1000 && pageSize in 1..50)
        val filtered =
            entries
                .filter {
                    it.medium == medium &&
                        (query.format == "All" || it.format == query.format) &&
                        (query.genre == "All" || it.genre == query.genre) &&
                        normalized(it.title).contains(normalized(query.text)) &&
                        (
                            query.date.isEmpty() ||
                                java.time.Instant
                                    .ofEpochMilli(it.updatedAt)
                                    .atOffset(java.time.ZoneOffset.UTC)
                                    .toLocalDate()
                                    .toString() == query.date
                        )
                }.let { rows ->
                    when (query.order) {
                        "Latest" -> rows.sortedByDescending { it.updatedAt }
                        "Title" -> rows.sortedBy { normalized(it.title) }
                        else -> rows
                    }
                }
        val start = (page - 1) * pageSize
        return EntryPage(filtered.drop(start).take(pageSize), start + pageSize < filtered.size)
    }

    private fun normalized(text: String) =
        Normalizer
            .normalize(text, Normalizer.Form.NFKD)
            .replace(Regex("\\p{M}+"), "")
            .lowercase(Locale.ROOT)
            .trim()
}

/** One bounded catalogue cache per source; concurrent Home sections share one request. */
class SiteRepository(
    val address: SiteAddress,
    private val load: suspend (String) -> String,
    private val now: () -> Long = System::nanoTime,
) {
    private val mutex = Mutex()
    private var saved: Pair<Long, List<Entry>>? = null

    suspend fun catalogue(): List<Entry> =
        mutex.withLock {
            saved?.takeIf { now() - it.first in 0..60_000_000_000L }?.second
                ?: SiteParser.catalogue(load(address.url("api/catalogue.json")), address).also { saved = now() to it }
        }

    suspend fun details(reference: String) = SiteParser.details(load(address.url(reference)), address)

    suspend fun streams(reference: String) = SiteParser.streams(load(address.url(reference)), address)

    suspend fun pages(reference: String) = SiteParser.pages(load(address.url(reference)), address)
}
