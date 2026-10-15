package example.placeholder.video

import eu.kanade.tachiyomi.animesource.AnimeSourceFactory
import eu.kanade.tachiyomi.animesource.model.AnimeFilter
import eu.kanade.tachiyomi.animesource.model.AnimeFilterList
import eu.kanade.tachiyomi.animesource.model.AnimesPage
import eu.kanade.tachiyomi.animesource.model.Hoster
import eu.kanade.tachiyomi.animesource.model.SAnime
import eu.kanade.tachiyomi.animesource.model.SEpisode
import eu.kanade.tachiyomi.animesource.model.Track
import eu.kanade.tachiyomi.animesource.model.Video
import eu.kanade.tachiyomi.animesource.online.AnimeHttpSource
import example.placeholder.common.Entry
import example.placeholder.common.Part
import example.placeholder.common.Query
import example.placeholder.common.SiteAddress
import example.placeholder.common.SiteParser
import example.placeholder.common.SiteRepository
import example.placeholder.common.readText
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.Request
import okhttp3.Response
import java.util.concurrent.TimeUnit

class VideoFactory : AnimeSourceFactory {
    override fun createSources() = listOf(VideoSource())
}

/** All website knowledge is here or in the extension's common parser module. */
class VideoSource : AnimeHttpSource() {
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
    private val site by lazy { SiteRepository(address, { readText(client, it, headers) }) }

    override fun getFilterList() = AnimeFilterList(Genre(), Format(), Order(), PublishedDate())

    private class Genre : AnimeFilter.Select<String>("Genre", arrayOf("All", "Adventure", "Slice of life", "Fantasy"))

    private class Format : AnimeFilter.Select<String>("Format", arrayOf("All", "Animation", "Cartoons"))

    private class Order : AnimeFilter.Select<String>("Order", arrayOf("Popular", "Latest", "Title"))

    private class PublishedDate : AnimeFilter.Text("Published date")

    private fun options(
        query: String,
        filters: AnimeFilterList,
    ): Query {
        fun selection(name: String) =
            filters
                .filterIsInstance<AnimeFilter.Select<*>>()
                .firstOrNull { it.name == name }
                ?.let { it.values.getOrNull(it.state)?.toString() }
        return Query(
            query,
            selection("Genre") ?: "All",
            selection("Order") ?: "Popular",
            filters
                .filterIsInstance<AnimeFilter.Text>()
                .firstOrNull()
                ?.state
                .orEmpty(),
            selection("Format") ?: "All",
        )
    }

    private suspend fun list(
        page: Int,
        query: Query,
    ): AnimesPage {
        val result = SiteParser.page(site.catalogue(), "anime", page, query)
        return AnimesPage(result.entries.map(::asAnime), result.hasNext)
    }

    override suspend fun getPopularAnime(page: Int) = list(page, Query())

    override suspend fun getLatestUpdates(page: Int) = list(page, Query(order = "Latest"))

    override suspend fun getSearchAnime(
        page: Int,
        query: String,
        filters: AnimeFilterList,
    ) = list(page, options(query, filters))

    override suspend fun getAnimeDetails(anime: SAnime) = asAnime(site.details(anime.url).entry)

    override suspend fun getEpisodeList(anime: SAnime) = site.details(anime.url).parts.map(::episode)

    override suspend fun getSeasonList(anime: SAnime): List<SAnime> = emptyList()

    override suspend fun getHosterList(episode: SEpisode) =
        listOf(
            Hoster(
                hosterUrl = address.url(episode.url),
                hosterName = "Original demo media",
            ),
        )

    override suspend fun getVideoList(hoster: Hoster) =
        site.streams(hoster.hosterUrl).map { stream ->
            Video(
                videoUrl = stream.url,
                videoTitle = stream.label,
                resolution = stream.resolution,
                subtitleTracks = stream.subtitles.map { Track(it.first, it.second) },
                initialized = true,
            )
        }

    private fun asAnime(entry: Entry) =
        SAnime.create().apply {
            url = entry.url
            title = entry.title
            thumbnail_url = entry.cover
            background_url = entry.banner
            description = entry.description
            author = "Placeholder Studio"
            artist = "Placeholder Studio"
            genre = entry.genre
            status = SAnime.COMPLETED
            initialized = true
            // Do not invent MAL/AniList IDs. Add only verified external IDs when adapting this source.
        }

    private fun episode(part: Part) =
        SEpisode.create().apply {
            url = part.url
            name = part.name
            episode_number = part.number
            date_upload = part.publishedAt
            summary = "Original synthetic demonstration episode"
            fillermark = false
        }

    // Retain coherent HTTP hooks for hosts using the original API entry points.
    private fun request(reference: String) = Request.Builder().url(address.url(reference)).headers(headers).build()

    private fun listingRequest(page: Int, query: Query): Request {
        require(page in 1..1000)
        val url = address.url("api/catalogue.json").toHttpUrl().newBuilder()
            .addQueryParameter("page", page.toString())
            .addQueryParameter("q", query.text)
            .addQueryParameter("genre", query.genre)
            .addQueryParameter("order", query.order)
            .addQueryParameter("date", query.date)
            .addQueryParameter("format", query.format)
            .build()
        return Request.Builder().url(url).headers(headers).build()
    }

    override fun popularAnimeRequest(page: Int) = listingRequest(page, Query())
    override fun latestUpdatesRequest(page: Int) = listingRequest(page, Query(order = "Latest"))
    override fun searchAnimeRequest(page: Int, query: String, filters: AnimeFilterList) = listingRequest(page, options(query, filters))

    override fun popularAnimeParse(response: Response) = response.use {
        val url = it.request.url
        val query = Query(url.queryParameter("q").orEmpty(), url.queryParameter("genre") ?: "All",
            url.queryParameter("order") ?: "Popular", url.queryParameter("date").orEmpty(), url.queryParameter("format") ?: "All")
        SiteParser.page(SiteParser.catalogue(it.body.string(), address), "anime", url.queryParameter("page")?.toIntOrNull() ?: 1, query)
            .let { result -> AnimesPage(result.entries.map(::asAnime), result.hasNext) }
    }
    override fun latestUpdatesParse(response: Response) = popularAnimeParse(response)
    override fun searchAnimeParse(response: Response) = popularAnimeParse(response)
    override fun animeDetailsRequest(anime: SAnime) = request(anime.url)
    override fun episodeListRequest(anime: SAnime) = request(anime.url)
    override fun animeDetailsParse(response: Response) = response.use { asAnime(SiteParser.details(it.body.string(), address).entry) }
    override fun episodeListParse(response: Response) = response.use { SiteParser.details(it.body.string(), address).parts.map(::episode) }
    override fun seasonListParse(response: Response): List<SAnime> = emptyList()
    override fun hosterListRequest(episode: SEpisode) = request(episode.url)
    override fun hosterListParse(response: Response) = response.use {
        listOf(Hoster(hosterUrl = it.request.url.toString(), hosterName = "Original demo media"))
    }
    override fun videoListParse(response: Response, hoster: Hoster) = response.use {
        SiteParser.streams(it.body.string(), address).map { stream ->
            Video(videoUrl = stream.url, videoTitle = stream.label, resolution = stream.resolution,
                subtitleTracks = stream.subtitles.map { Track(it.first, it.second) }, initialized = true)
        }
    }
}
