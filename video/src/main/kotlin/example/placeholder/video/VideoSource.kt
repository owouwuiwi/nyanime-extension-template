package example.placeholder.video

import eu.kanade.tachiyomi.animesource.AnimeSourceFactory
import eu.kanade.tachiyomi.animesource.model.AnimeFilter
import eu.kanade.tachiyomi.animesource.model.AnimeFilterList
import eu.kanade.tachiyomi.animesource.model.AnimesPage
import eu.kanade.tachiyomi.animesource.model.Hoster
import eu.kanade.tachiyomi.animesource.model.SAnime
import eu.kanade.tachiyomi.animesource.model.SAnimeEpisodeUpdate
import eu.kanade.tachiyomi.animesource.model.SAnimeSeasonUpdate
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
import kotlinx.serialization.json.add
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import java.util.concurrent.TimeUnit

class VideoFactory : AnimeSourceFactory {
    override fun createSources() = listOf(VideoSource())
}

/** All website knowledge is here or in the extension's common parser module. */
class VideoSource : AnimeHttpSource() {
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

    // One HTML fetch when details and episodes are requested together: no duplicated extraction.
    override suspend fun getAnimeEpisodeUpdate(
        anime: SAnime,
        episodes: List<SEpisode>,
        fetchDetails: Boolean,
        fetchEpisodes: Boolean,
    ): SAnimeEpisodeUpdate {
        if (!fetchDetails && !fetchEpisodes) return SAnimeEpisodeUpdate(anime, episodes)
        val details = site.details(anime.url)
        return SAnimeEpisodeUpdate(
            if (fetchDetails) asAnime(details.entry) else anime,
            if (fetchEpisodes) details.parts.map(::episode) else episodes,
        )
    }

    override suspend fun getAnimeSeasonUpdate(
        anime: SAnime,
        seasons: List<SAnime>,
        fetchDetails: Boolean,
        fetchSeasons: Boolean,
    ) = SAnimeSeasonUpdate(if (fetchDetails) getAnimeDetails(anime) else anime, if (fetchSeasons) emptyList() else seasons)

    override suspend fun getHosterList(episode: SEpisode) =
        listOf(
            Hoster(
                hosterUrl = address.url(episode.url),
                hosterName = "Original demo media",
                memo =
                    buildJsonObject {
                    },
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
                                    add(entry.format)
                                },
                            )
                        },
                    )
                }
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
}
