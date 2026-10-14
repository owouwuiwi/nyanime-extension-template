package example.placeholder.tv

import example.placeholder.common.SiteAddress
import example.placeholder.common.SiteParser
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import nyanime.tv.api.TvCapabilities
import nyanime.tv.api.TvCatalogue
import nyanime.tv.api.TvCatalogueRequest
import nyanime.tv.api.TvChannel
import nyanime.tv.api.TvChannelLookup
import nyanime.tv.api.TvChannelRef
import nyanime.tv.api.TvFacet
import nyanime.tv.api.TvGuide
import nyanime.tv.api.TvGuideAvailability
import nyanime.tv.api.TvGuideRequest
import nyanime.tv.api.TvHomeSection
import nyanime.tv.api.TvHttpClient
import nyanime.tv.api.TvPlayback
import nyanime.tv.api.TvSource
import nyanime.tv.api.TvSourceCache
import nyanime.tv.api.TvSourceFactory
import nyanime.tv.api.TvStream

class TvFactory : TvSourceFactory {
    override fun create(
        http: TvHttpClient,
        cache: TvSourceCache,
    ) = listOf(DemoTv(http))
}

/** A finite synthetic signal demonstrates the API; this is not a real live broadcaster. */
class DemoTv(
    private val http: TvHttpClient,
) : TvSource {
    override val id = BuildConfig.SOURCE_ID
    override val name = BuildConfig.SOURCE_NAME
    override val language = BuildConfig.LANGUAGE
    override val capabilities =
        TvCapabilities(
            homeTitle = mapOf("en" to "DEMO TV", "it" to "DEMO TV"),
            initialCountry = "IT",
            guide = false,
            countries = listOf(TvFacet("IT", mapOf("en" to "Italy", "it" to "Italia"))),
            languages = listOf(TvFacet("en", mapOf("en" to "English"))),
            categories = listOf(TvFacet("demo", mapOf("en" to "Synthetic signals", "it" to "Segnali dimostrativi"))),
            attribution = "Original finite test signal · CC0-1.0 · not a live broadcast",
            channelLookup = true,
        )
    private val address = SiteAddress(BuildConfig.BASE_URL)

    private suspend fun rows(): List<JsonObject> {
        val response = http.get(address.url("api/tv.json"), emptyMap())
        require(response.code in 200..299) { "TV catalogue is temporarily unavailable" }
        address.url(response.finalUrl)
        return SiteParser.objectFrom(response.body)["channels"]!!.jsonArray.map { it.jsonObject }
    }

    private fun asChannel(row: JsonObject) =
        TvChannel(
            TvChannelRef(id, row["id"]!!.jsonPrimitive.content),
            row["name"]!!.jsonPrimitive.content,
            address.url(row["logo"]!!.jsonPrimitive.content),
            country = "IT",
            languages = setOf("en"),
            categories = setOf("demo"),
            feedName = "Finite demonstration",
            guide = TvGuideAvailability.NONE,
        )

    override suspend fun catalogue(request: TvCatalogueRequest): TvCatalogue {
        require(request.cursor == null) { "This finite catalogue has no next page" }
        val compatible =
            (request.country == null || request.country == "IT") &&
                (request.language == null || request.language == "en") &&
                (request.category == null || request.category == "demo")
        val channels = if (compatible) rows().map(::asChannel) else emptyList()
        return TvCatalogue(channels, sections = listOf(TvHomeSection("demo", mapOf("en" to "Synthetic signal"), channels.map { it.ref })))
    }

    override suspend fun channels(references: List<TvChannelRef>): TvChannelLookup {
        val available = rows().map(::asChannel).filter { it.ref in references }
        return TvChannelLookup(available, unavailable = references.toSet() - available.map { it.ref }.toSet())
    }

    override suspend fun programmes(request: TvGuideRequest) = TvGuide(emptyList(), unavailable = request.channels.toSet())

    override suspend fun resolve(channel: TvChannelRef): TvPlayback {
        require(channel.sourceId == id) { "Channel belongs to another source" }
        val row = rows().singleOrNull { it["id"]!!.jsonPrimitive.content == channel.id } ?: error("Channel is no longer available")
        return TvPlayback(
            asChannel(row),
            listOf(
                TvStream(
                    "synthetic",
                    address.url(row["stream"]!!.jsonPrimitive.content),
                    "Original finite sample · no live clock",
                    resolution = 180,
                    mimeType = "video/mp4",
                    rewind = false,
                    adjustableSpeed = false,
                    clock = null,
                ),
            ),
        )
    }
}
