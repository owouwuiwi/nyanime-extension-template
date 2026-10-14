package example.placeholder.news

import example.placeholder.common.SiteAddress
import example.placeholder.common.SiteParser
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.longOrNull
import nyanime.news.api.NewsArticle
import nyanime.news.api.NewsBlock
import nyanime.news.api.NewsBlockKind
import nyanime.news.api.NewsCapabilities
import nyanime.news.api.NewsCategory
import nyanime.news.api.NewsHttpClient
import nyanime.news.api.NewsMedium
import nyanime.news.api.NewsPage
import nyanime.news.api.NewsRequest
import nyanime.news.api.NewsSource
import nyanime.news.api.NewsSourceFactory

class NewsFactory : NewsSourceFactory {
    override fun create(http: NewsHttpClient): NewsSource = DemoNews(http)
}

class DemoNews(
    private val http: NewsHttpClient,
) : NewsSource {
    override val name = BuildConfig.SOURCE_NAME
    override val language = BuildConfig.LANGUAGE
    override val capabilities =
        NewsCapabilities(
            search = true,
            media = setOf(NewsMedium.ANIME, NewsMedium.MANGA),
            categories = listOf(NewsCategory("development", "Development")),
        )
    private val address = SiteAddress(BuildConfig.BASE_URL)

    private suspend fun load(reference: String): String {
        val response = http.get(address.url(reference), emptyMap())
        address.url(response.finalUrl)
        return response.body
    }

    private fun JsonObject.text(key: String) = this[key]!!.jsonPrimitive.content

    private fun asArticle(
        value: JsonObject,
        full: Boolean,
    ) = NewsArticle(
        id = value.text("id"),
        url = address.url(value.text("url")),
        title = value.text("title"),
        publisher = "Placeholder Studio",
        language = language,
        publishedAt = value["publishedAt"]?.jsonPrimitive?.longOrNull,
        imageUrl = address.url(value.text("image")),
        excerpt = value.text("excerpt"),
        media = setOf(NewsMedium.valueOf(value.text("medium"))),
        categories = setOf(value.text("category")),
        blocks =
            if (full) {
                listOf(
                    NewsBlock(NewsBlockKind.HEADING, value.text("title")),
                    NewsBlock(NewsBlockKind.TEXT, value.text("body")),
                    NewsBlock(NewsBlockKind.IMAGE, url = address.url(value.text("image")), caption = "Original geometric demo artwork"),
                )
            } else {
                emptyList()
            },
        fullText = full,
        attribution = "Original sample text · CC0-1.0",
    )

    override suspend fun feed(request: NewsRequest) = results("", request)

    override suspend fun search(
        query: String,
        request: NewsRequest,
    ) = results(query, request)

    private suspend fun results(
        query: String,
        request: NewsRequest,
    ): NewsPage {
        val start =
            request.cursor?.toIntOrNull()?.also { require(it in 0..1000) }
                ?: if (request.cursor == null) 0 else error("Invalid page cursor")
        val rows =
            SiteParser
                .objectFrom(load("api/news.json"))["articles"]!!
                .jsonArray
                .map { asArticle(it.jsonObject, false) }
                .filter {
                    it.title.contains(query, ignoreCase = true) &&
                        (request.medium == null || request.medium in it.media) &&
                        (request.category == null || request.category in it.categories)
                }
        return NewsPage(rows.drop(start).take(3), (start + 3).takeIf { it < rows.size }?.toString())
    }

    override suspend fun article(article: NewsArticle): NewsArticle {
        val result = asArticle(SiteParser.dataFromHtml(load(article.url)), true)
        require(result.id == article.id && result.url == article.url) { "Article identity changed" }
        return result
    }
}
