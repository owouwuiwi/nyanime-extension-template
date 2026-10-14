package example.placeholder.manga

import eu.kanade.tachiyomi.source.SourceFactory
import eu.kanade.tachiyomi.source.model.Filter
import eu.kanade.tachiyomi.source.model.FilterList
import eu.kanade.tachiyomi.source.model.MangasPage
import eu.kanade.tachiyomi.source.model.Page
import eu.kanade.tachiyomi.source.model.SChapter
import eu.kanade.tachiyomi.source.model.SManga
import eu.kanade.tachiyomi.source.model.SMangaHomeMetadata
import eu.kanade.tachiyomi.source.model.SMangaUpdate
import eu.kanade.tachiyomi.source.online.HttpSource
import example.placeholder.common.Entry
import example.placeholder.common.Part
import example.placeholder.common.Query
import example.placeholder.common.SiteAddress
import example.placeholder.common.SiteParser
import example.placeholder.common.SiteRepository
import example.placeholder.common.readText
import kotlinx.serialization.json.add
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.Request
import okhttp3.Response
import java.util.concurrent.TimeUnit

class MangaFactory : SourceFactory {
    override fun createSources() = listOf(MangaSource())
}

class MangaSource : HttpSource() {
    override val id = BuildConfig.SOURCE_ID
    override val name = BuildConfig.SOURCE_NAME
    override val lang = BuildConfig.LANGUAGE
    override val baseUrl = BuildConfig.BASE_URL.removeSuffix("/")
    override val supportsLatest = true
    override val client by lazy {
        network.client
            .newBuilder()
            .followRedirects(false)
            .followSslRedirects(false)
            .callTimeout(15, TimeUnit.SECONDS)
            .build()
    }
    private val address = SiteAddress(BuildConfig.BASE_URL)
    private val site by lazy { SiteRepository(address, { readText(client, it, headers) }) }

    private class Genre : Filter.Select<String>("Genre", arrayOf("All", "Adventure", "Slice of life", "Fantasy"))

    private class Order : Filter.Select<String>("Order", arrayOf("Popular", "Latest", "Title"))

    private class PublishedDate : Filter.Text("Published date")

    override fun getFilterList() = FilterList(Genre(), Order(), PublishedDate())

    private fun options(
        query: String,
        filters: FilterList,
    ): Query {
        fun selection(name: String) =
            filters.filterIsInstance<Filter.Select<*>>().firstOrNull { it.name == name }?.let { it.values.getOrNull(it.state)?.toString() }
        return Query(
            query,
            selection("Genre") ?: "All",
            selection("Order") ?: "Popular",
            filters
                .filterIsInstance<Filter.Text>()
                .firstOrNull()
                ?.state
                .orEmpty(),
        )
    }

    private suspend fun list(
        page: Int,
        query: Query,
    ): MangasPage {
        val result = SiteParser.page(site.catalogue(), "manga", page, query)
        return MangasPage(result.entries.map(::asManga), result.hasNext)
    }

    override suspend fun getPopularManga(page: Int) = list(page, Query())

    override suspend fun getLatestUpdates(page: Int) = list(page, Query(order = "Latest"))

    override suspend fun getSearchManga(
        page: Int,
        query: String,
        filters: FilterList,
    ) = list(page, options(query, filters))

    override suspend fun getMangaDetails(manga: SManga) = asManga(site.details(manga.url).entry)

    override suspend fun getChapterList(manga: SManga) = site.details(manga.url).parts.map(::chapter)

    override suspend fun getPageList(chapter: SChapter) = site.pages(chapter.url).mapIndexed { index, url -> Page(index, imageUrl = url) }

    override suspend fun getMangaUpdate(
        manga: SManga,
        chapters: List<SChapter>,
        fetchDetails: Boolean,
        fetchChapters: Boolean,
    ): SMangaUpdate {
        if (!fetchDetails && !fetchChapters) return SMangaUpdate(manga, chapters)
        val details = site.details(manga.url)
        return SMangaUpdate(
            if (fetchDetails) asManga(details.entry) else manga,
            if (fetchChapters) details.parts.map(::chapter) else chapters,
        )
    }

    private fun asManga(entry: Entry) =
        SManga.create().apply {
            url = entry.url
            title = entry.title
            thumbnail_url = entry.cover
            description = entry.description
            author = "Placeholder Studio"
            artist = "Placeholder Studio"
            genre = entry.genre
            status = SManga.COMPLETED
            initialized = true
            memo =
                buildJsonObject {
                    put(
                        "aniyomi.home.v1",
                        buildJsonObject {
                            put("version", 1)
                            put("logoUrl", address.url("images/logo.png"))
                            put("logoName", "Placeholder Studio")
                            put("logoBackground", "dark")
                            put(
                                "badges",
                                buildJsonArray {
                                    add("DEMO")
                                    add("Original artwork")
                                },
                            )
                        },
                    )
                }
            (this as? SMangaHomeMetadata)?.homePresentation = memo["aniyomi.home.v1"].toString()
        }

    private fun chapter(part: Part) =
        SChapter.create().apply {
            url = part.url
            name = part.name
            chapter_number = part.number
            date_upload =
                part.publishedAt
        }

    // The abstract HTTP/Rx hooks remain coherent for older callers of this source API.
    private fun request(reference: String) =
        Request
            .Builder()
            .url(address.url(reference))
            .headers(headers)
            .build()

    private fun listingRequest(
        page: Int,
        query: Query,
    ): Request {
        require(page in 1..1000)
        val url =
            address
                .url("api/catalogue.json")
                .toHttpUrl()
                .newBuilder()
                .addQueryParameter("page", page.toString())
                .addQueryParameter("q", query.text)
                .addQueryParameter("genre", query.genre)
                .addQueryParameter("order", query.order)
                .addQueryParameter("date", query.date)
                .build()
        return Request
            .Builder()
            .url(url)
            .headers(headers)
            .build()
    }

    override fun popularMangaRequest(page: Int) = listingRequest(page, Query())

    override fun latestUpdatesRequest(page: Int) = listingRequest(page, Query(order = "Latest"))

    override fun searchMangaRequest(
        page: Int,
        query: String,
        filters: FilterList,
    ) = listingRequest(page, options(query, filters))

    override fun popularMangaParse(response: Response) =
        response.use {
            val url = it.request.url
            val query =
                Query(
                    url.queryParameter("q").orEmpty(),
                    url.queryParameter("genre") ?: "All",
                    url.queryParameter("order") ?: "Popular",
                    url.queryParameter("date").orEmpty(),
                )
            SiteParser
                .page(
                    SiteParser.catalogue(it.body.string(), address),
                    "manga",
                    url.queryParameter("page")?.toIntOrNull() ?: 1,
                    query,
                ).let { page ->
                    MangasPage(page.entries.map(::asManga), page.hasNext)
                }
        }

    override fun latestUpdatesParse(response: Response) = popularMangaParse(response)

    override fun searchMangaParse(response: Response) = popularMangaParse(response)

    override fun mangaDetailsRequest(manga: SManga) = request(manga.url)

    override fun chapterListRequest(manga: SManga) = request(manga.url)

    override fun pageListRequest(chapter: SChapter) = request(chapter.url)

    override fun mangaDetailsParse(response: Response) = response.use { asManga(SiteParser.details(it.body.string(), address).entry) }

    override fun chapterListParse(response: Response) = response.use { SiteParser.details(it.body.string(), address).parts.map(::chapter) }

    override fun chapterPageParse(response: Response): SChapter = error("Chapter pagination is not published by this demo")

    override fun pageListParse(response: Response) =
        response.use {
            SiteParser.pages(it.body.string(), address).mapIndexed { index, url -> Page(index, imageUrl = url) }
        }

    override fun imageUrlParse(response: Response): String = response.use { error("Page images already have final image URLs") }
}
