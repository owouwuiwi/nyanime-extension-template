package example.placeholder.manga

import eu.kanade.tachiyomi.source.SourceFactory
import eu.kanade.tachiyomi.source.model.Filter
import eu.kanade.tachiyomi.source.model.FilterList
import eu.kanade.tachiyomi.source.model.MangasPage
import eu.kanade.tachiyomi.source.model.Page
import eu.kanade.tachiyomi.source.model.SChapter
import eu.kanade.tachiyomi.source.model.SManga
import eu.kanade.tachiyomi.source.online.HttpSource
import example.placeholder.common.Entry
import example.placeholder.common.Part
import example.placeholder.common.Query
import example.placeholder.common.SiteAddress
import example.placeholder.common.SiteParser
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
    private val address = SiteAddress(BuildConfig.BASE_URL)
    override val baseUrl = address.origin
    override val supportsLatest = true
    override val client by lazy {
        network.client
            .newBuilder()
            .followRedirects(false)
            .followSslRedirects(false)
            .callTimeout(15, TimeUnit.SECONDS)
            .build()
    }

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

    override fun pageListParse(response: Response) =
        response.use {
            SiteParser.pages(it.body.string(), address).mapIndexed { index, url -> Page(index, imageUrl = url) }
        }

    override fun imageUrlParse(response: Response): String = response.use { error("Page images already have final image URLs") }
}
