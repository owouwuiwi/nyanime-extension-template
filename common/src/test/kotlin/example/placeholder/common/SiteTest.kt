package example.placeholder.common

import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Assert.fail
import org.junit.Test
import java.io.File
import java.util.concurrent.atomic.AtomicInteger

class SiteTest {
    private val root = File(System.getProperty("fixtureRoot"))
    private val address = SiteAddress("https://fixture.invalid/example/")

    private fun load(reference: String) =
        File(root, reference.removePrefix("/example/")).let {
            (if (it.isDirectory) File(it, "index.html") else it).readText()
        }

    private fun catalogue() = SiteParser.catalogue(load("api/catalogue.json"), address)

    private fun fails(action: () -> Unit) {
        try {
            action()
            fail("Expected rejected input")
        } catch (_: IllegalArgumentException) {
        }
    }

    @Test fun categoriesScopeTheirOwnData() {
        val all = catalogue()
        val animation = SiteParser.page(all, "anime", 1, Query(format = "Animation"), 50)
        val cartoons = SiteParser.page(all, "anime", 1, Query(format = "Cartoons"), 50)
        assertEquals(6, animation.entries.size)
        assertEquals(3, cartoons.entries.size)
        assertTrue(animation.entries.none { it in cartoons.entries })
        assertEquals(6, SiteParser.page(all, "manga", 1, Query(), 50).entries.size)
    }

    @Test fun filteredPaginationDoesNotRepeatOrInventMorePages() {
        val all = catalogue()
        val first = SiteParser.page(all, "anime", 1, Query(format = "Animation"))
        val second = SiteParser.page(all, "anime", 2, Query(format = "Animation"))
        assertTrue(first.hasNext)
        assertFalse(second.hasNext)
        assertEquals(6, (first.entries + second.entries).map { it.id }.distinct().size)
        assertTrue(SiteParser.page(all, "anime", 3, Query(format = "Animation")).entries.isEmpty())
    }

    @Test fun queryGenreDateAndOrderingArePreserved() {
        val all = catalogue()
        val target = all.first()
        val result = SiteParser.page(all, "anime", 1, Query(text = target.title.uppercase(), genre = target.genre))
        assertEquals(listOf(target), result.entries)
        assertTrue(SiteParser.page(all, "anime", 1, Query(date = "1999-01-01")).entries.isEmpty())
        val latest = SiteParser.page(all, "anime", 1, Query(order = "Latest"), 50).entries
        assertEquals(latest.map { it.updatedAt }.sortedDescending(), latest.map { it.updatedAt })
        fails { SiteParser.page(all, "anime", 0, Query()) }
    }

    @Test fun detailsUseStableReferencesAndPublishedDates() {
        val entry = catalogue().first { it.medium == "manga" }
        val details = SiteParser.details(load(entry.url), address)
        assertEquals(entry.id, details.entry.id)
        assertEquals(listOf(3f, 2f, 1f), details.parts.map { it.number })
        assertTrue(details.parts.all { it.url.startsWith("/example/") && it.publishedAt > 0 })
    }

    @Test fun pagesRetainPublishedOrderIncludingOddChapters() {
        val entry = catalogue().first { it.medium == "manga" }
        val parts = SiteParser.details(load(entry.url), address).parts
        val even = SiteParser.pages(load(parts.first { it.number == 1f }.url), address)
        val odd = SiteParser.pages(load(parts.first { it.number == 2f }.url), address)
        assertEquals(6, even.size)
        assertEquals(5, odd.size)
        assertTrue(even.first().endsWith("01.png"))
        assertTrue(even.last().endsWith("06.png"))
    }

    @Test fun videoQualitiesAndSubtitleUrlsAreExtractedFromHtml() {
        val entry = catalogue().first { it.medium == "anime" }
        val episode = SiteParser.details(load(entry.url), address).parts.first()
        val streams = SiteParser.streams(load(episode.url), address)
        assertEquals(setOf(180, 360), streams.map { it.resolution }.toSet())
        assertTrue(
            streams.all {
                it.subtitles
                    .single()
                    .first
                    .endsWith("demo-en.vtt")
            },
        )
    }

    @Test fun addressCannotEscapeTheAdapterArea() {
        listOf(
            "https://other.invalid/example/a",
            "../secret",
            "/other/path",
            "//other.invalid/a",
            "%2e%2e/secret",
            "images%2fsecret",
            "images\\secret",
            "images/a?token=x",
            "images/a#x",
            "https://user@fixture.invalid/example/a",
        ).forEach { fails { address.url(it) } }
        assertEquals("https://fixture.invalid/example/images/a.png", address.url("images/a.png"))
    }

    @Test fun malformedAndMissingContentDoesNotBecomeFakeResults() {
        fails { SiteParser.catalogue("{\"schema\":2,\"entries\":[]}", address) }
        assertThrows(IllegalStateException::class.java) { SiteParser.dataFromHtml("<html>Changed markup</html>") }
        fails { SiteParser.pages("<main class=reader></main>", address) }
        fails { SiteParser.streams("<video></video>", address) }
    }

    @Test fun concurrentSectionsShareOneBoundedCatalogueFetch() =
        runBlocking {
            val count = AtomicInteger()
            var clock = 0L
            val repository =
                SiteRepository(address, {
                    count.incrementAndGet()
                    delay(20)
                    load("api/catalogue.json")
                }, { clock })
            coroutineScope { List(8) { async { repository.catalogue() } }.awaitAll() }
            assertEquals(1, count.get())
            clock = 61_000_000_000L
            repository.catalogue()
            assertEquals(2, count.get())
        }

    @Test fun failuresAndCancellationNeverPopulateTheCache() =
        runBlocking {
            var attempts = 0
            val repository =
                SiteRepository(address, {
                    attempts++
                    when (attempts) {
                        1 -> throw java.io.IOException("Offline")
                        2 -> throw CancellationException("Obsolete request")
                        else -> load("api/catalogue.json")
                    }
                })
            try {
                repository.catalogue()
                fail("Expected offline error")
            } catch (_: java.io.IOException) {
            }
            try {
                repository.catalogue()
                fail("Expected cancellation")
            } catch (_: CancellationException) {
            }
            assertEquals(15, repository.catalogue().size)
            repository.catalogue()
            assertEquals(3, attempts)
        }
}
