# Build a Nyanime extension

One complete guide: understand the APIs, adapt a website, declare Home categories,
build, sign, install and maintain an extension. Start with the unchanged example,
then follow the section for your source family. You do not need to change Nyanime.

The examples use original geometric drawings, sample articles and intentionally
black, silent videos from [the playground](https://owouwuiwi.github.io/example/).
**Nyanime does not promote piracy in any way or form.** Bring your own content and
use only material you are legally entitled to access.
[Read our position](https://owouwuiwi.github.io/responsible-use/).

This guide targets the exported SDK in [sdk-lock.json](../sdk/sdk-lock.json).
That file records the host revision, source hashes and API JAR hashes. New optional
capabilities may require a newer host; they are not supported by every old version.

## Architecture and ownership

An extension implements a **Kotlin API loaded by Nyanime**. This is different
from a website's HTTP API: your extension fetches HTML or JSON, parses it, and
returns the typed models that Nyanime understands.

```text
User opens Home, searches, plays or reads
  → Nyanime calls a public source method
  → the extension requests and parses its website
  → the extension returns typed data
  → Nyanime renders it and owns playback, reading and progress
```

| Layer | Owns |
| --- | --- |
| Nyanime | Navigation, Home rendering, search coordination, library, progress, cache, player, reader, Cast, rooms, backup and installation/trust UI |
| Shared API | Typed source models and public capability contracts |
| Extension | Website addresses, selectors, parsing, pagination, source IDs, stream resolution, programme matching and source-specific rules |
| Demo website | Public test fixtures and original media; replace it when adapting the source |

Extensions execute code in the host process after approval. **RIN is a signed
package format, not a security sandbox.** Never request unrelated permissions,
inspect host databases, depend on private host classes or run permanent services.
Use public APIs and cancellation-aware network calls. Approval is explicit;
installation must never silently trust a publisher.

Shared APIs and libraries are `compileOnly`. Bundle your implementation only.
`pack.py` inspects DEX class definitions and rejects accidentally bundled host,
Kotlin, networking or parsing libraries. Keep the default implementation namespace
while learning; if changing it, update the packer's allowed namespace too.

The SDK export includes source-api, core-common, news-api, tv-api and addon-api.
Each module uses only the contracts it needs. Keep SDK dependencies aligned with
the target host; do not confuse an extension build library with the runtime API.

## Choosing a family

| Family | Entry point | Public operations | Current starter distribution |
| --- | --- | --- | --- |
| Video | `AnimeSourceFactory` → `AnimeHttpSource` | Popular/latest/search, details, episodes, seasons, hosters, videos | RIN schema 1, `medium: anime`, API 17 |
| Manga | `SourceFactory` → `HttpSource` | Popular/latest/search, details, chapters, pages, image loading | RIN schema 1, `medium: manga`, API 1.6 |
| News | `NewsSourceFactory.create(NewsHttpClient)` | Feed, optional search, complete article | APK, News API 1 |
| TV | `TvSourceFactory.create(http, cache)` | Catalogue, channel lookup, guide, playback resolution | RIN schema 2, `medium: tv`, API 1 |

These are four working sources, not four mandatory dependencies. News RIN import
is not implemented by the current host; do not label an APK as a `.rin`.
Guide and addon extension families have separate contracts described below;
they are not disguised video sources or required to implement this starter.

Read the working implementations alongside this guide:
[video](../video/src/main/kotlin/example/placeholder/video/VideoSource.kt),
[manga](../manga/src/main/kotlin/example/placeholder/manga/MangaSource.kt),
[news](../news/src/main/kotlin/example/placeholder/news/NewsSource.kt) and
[TV](../tv/src/main/kotlin/example/placeholder/tv/TvSource.kt).
Exact public interfaces are included locally in
[video API](../sdk/sources/source-api/src/commonMain/kotlin/eu/kanade/tachiyomi/animesource/AnimeSource.kt),
[manga API](../sdk/sources/source-api/src/commonMain/kotlin/eu/kanade/tachiyomi/source/Source.kt),
[news API](../sdk/sources/news-api/src/main/kotlin/nyanime/news/api/NewsSource.kt) and
[TV API](../sdk/sources/tv-api/src/main/kotlin/nyanime/tv/api/TvSource.kt).

## Set up and build the unchanged example

Use **Use this template** on the [starter repository](https://github.com/owouwuiwi/nyanime-extension-template),
clone it, or extract the [complete kit](https://owouwuiwi.github.io/example/downloads/placeholder-extension-kit.zip).
Open a terminal in the directory containing `template.json` and `gradlew`.

Install **JDK 17**, **Android SDK platform 36 / Build Tools 35.0.1** and
**Python 3.10+**. Set `JAVA_HOME` to the JDK directory. Set `ANDROID_HOME` to
the SDK directory, or create `local.properties` with `sdk.dir=/your/android/sdk`.
Android Studio's SDK Manager can install the specified platform and tools.
On Windows, replace `./gradlew` with `./gradlew.bat` in every command below.

```sh
python -m pip install -r requirements-tools.txt
python -m unittest discover -s tests -v
./gradlew :common:test :video:assembleDebug
```

This tests the parser and creates `video/build/outputs/apk/debug/video-debug.apk`.
For video/manga/TV, the APK is a **build container**: package it as RIN before
installation. News is distributed as an APK. Keep the public demo URL unchanged
for the first build; another website requires another parser.

The matching compile-only SDK and Gradle wrapper are included. Only when targeting
a different matching Nyanime checkout, export its API modules again:

```sh
python tools/prepare_sdk.py --host /path/to/nyanime --build
```

## Configure identity and discovery

Edit [template.json](../template.json), then run `python tools/configure.py`.

| Field | Meaning and update rule |
| --- | --- |
| `baseUrl` | HTTPS website directory ending in `/`; changing it alone does not adapt the parser |
| `language` | Two-letter source content language, such as `en`; not the device UI language |
| `modules.video.package` | Unique package identity; choose yours before publishing, then retain it |
| `modules.video.sourceId` | Stable positive signed 64-bit source ID, independent of local database rows |
| `modules.video.name` | Display name; Home's owned source selector must match it and its language |
| `versionCode` | Positive integer increased for each published change |
| `versionName` | Human-readable version, separate from the host compatibility floor |
| `minimumHostVersionCode` | Compatible host floor; at least `232` for this starter's local import path |

The same module fields exist for manga, news and TV. Keep all four declarations
even when building one module. Never distribute your own product with demo IDs.

`configure.py` generates Android manifests, icons, distribution metadata and
video/manga Home JSON. **It overwrites those generated files.** For lasting custom
Home declarations, change its `home()` generator, not only the generated JSON.

The configured package identity is separate from the Kotlin namespace
`example.placeholder.*`, which you can keep while learning. If renaming Kotlin
packages, also update factory names in `configure.py` and `pack.py`, Gradle
namespaces and the packer's DEX allowlist. The configuration does not rename code.

The host discovers factories through metadata: RIN's `manifest.json.entryPoints`
for video/manga/TV, and Android manifest `nyanime.news.factory` /
`nyanime.news.api` for News APKs. `configure.py` and `pack.py` register these for
you. Historical metadata/API namespaces are compatibility contracts: do not
rename them for branding.

## Read the website and map the data

Start in [common/Site.kt](../common/src/main/kotlin/example/placeholder/common/Site.kt).
`SiteAddress` resolves and validates links; `SiteParser` converts HTML/JSON into
`Entry`, `Part`, `Stream` and page lists; `SiteRepository` fetches data and shares
a bounded catalogue cache. Each `*Source.kt` maps those values to public API models.

| Fixture | Extraction | Result |
| --- | --- | --- |
| `api/catalogue.json` | JSON `schema` and `entries` | Searchable title summaries |
| A title page | `script#entry-data[type=application/json]`, then `entry` / `parts` | Details and episodes/chapters |
| An episode page | `video source[src]`, `data-label`, `data-height` | Playable qualities |
| An episode page | `video track[kind=subtitles][src]` | Subtitle URLs and languages |
| A chapter page | `main.reader img[data-page][src]` in document order | Ordered final page images |
| `api/news.json` and article pages | Feed records and structured body | News summaries and full articles |
| `api/tv.json` | Channel records | Channel metadata and playback references |

The demo is a small static site. `SiteParser.page()` filters/paginates a bounded
catalogue locally. For a large website with server pagination, translate query
and filters into requests and parse its next-page state instead of downloading
its entire catalogue. Changing websites means adapting requests, selectors,
field mapping and URL policy in the extension, never in Nyanime.

## Home categories, sections and filters

The signed asset `assets/aniyomi/home-v1.json` declares navigation. Its historical
path is a compatibility contract: do not rename it for branding.

```json
{
  "version": 1,
  "homes": [{
    "id": "cartoons",
    "title": "Cartoons",
    "source": {"name": "Your source", "lang": "en"},
    "defaults": {"Format": "Cartoons"},
    "browseFilters": ["Genre", "Order", "Published date"],
    "sections": [
      {"id": "featured", "title": "Highlights", "layout": "featured"},
      {"id": "latest", "title": "New releases", "filters": {"Order": "Latest"}},
      {"id": "day", "title": "On this day", "dateFilter": "Published date"}
    ],
    "search": {"id": "search", "title": "Search cartoons", "filters": {}},
    "categories": {"filter": "Genre", "exclude": ["All"]}
  }]
}
```

`source.name` and `source.lang` must identify exactly one source **owned by that
extension**. Each Home category has a stable semantic ID; its label is presentation.
There is no hardcoded list of permitted categories. Multiple `homes[]` entries
produce multiple destinations, subject to the user's enabled languages, visibility,
content settings and Home selection/order.

Separate extensions can deliberately contribute to the same semantic Home ID.
Video and reading Homes use separate navigation namespaces. Within one medium,
their sections with matching IDs are merged; unique sections are added. Agree
on semantics: `latest` must not mean popularity for one contributor. Titles alone
are not reliable identity or deduplication keys. Every result retains its source.

The starter uses **demo-prefixed category IDs** so installation does not take over
an existing destination. Its `Format` filter keeps Animation and Cartoons separate.
The app learns neither those format values nor any website rule.

Filter keys and values match the extension's **public filter labels**. Each call
to `getFilterList()` returns fresh objects. `defaults` apply throughout that Home;
section `filters` refine them. `moreFilters` can refine the full-list route.
`browseFilters` exposes supported select, checkbox group and text controls.
`categories.filter` supplies genre chips: it does **not** declare Home categories.
Unsupported filters must not silently become an unfiltered query.

`dateFilter` names a public Text filter receiving a civil `YYYY-MM-DD` date;
an empty value means the source's default day. The source owns timezone conversion.
Date/query/filter values remain attached to every page. `hasNext` must reflect
the filtered result, not the unfiltered catalogue.

Sections may declare `group: {id, title, tab}` to offer variants in one row.
`primary: true` can opt a Home into the initial destination; this starter leaves
it unset. Limits: version 1, 64 KiB, 8 Homes, 16 sections per Home, 100-character
labels. Keep IDs unique within one declaration and unknown values optional.

See the authoritative [Home contract](https://github.com/owouwuiwi/nyanime/blob/main/docs/extension-home-api.md)
and [manga Home additions](https://github.com/owouwuiwi/nyanime/blob/main/docs/manga-home-api.md).

## Covers, logos and rich presentation

Return `thumbnail_url` and, for video, `background_url` on normal source models.
Keep stable public URLs when the image has not changed so host image caches work.
An extension can extract the current horizontal logo from its website and return
it in `SAnime.memo["aniyomi.home.v1"]`, or manga's optional `SMangaHomeMetadata`:

```json
{"logoUrl":"https://your.example/logo.png","logoName":"Your source",
 "logoBackground":"dark","badges":["SUB"],"details":["Public source information"]}
```

The starter publishes a fixed original fixture logo. A real adapter owns dynamic
extraction. The host decides layout and respects the source-logo preference.
Never put cookies, signed private URLs or executable markup in presentation fields.
An optional event `id` can distinguish multiple episode cards for one title without
changing the title URL or creating duplicate library entries.

## Content identity, progress and metadata

For HttpSource adapters, `baseUrl` is the website origin while stored references
include the website directory. The starter verifies that host WebView links can
recompose them without duplicating `/example/`.

Source IDs are stable positive 64-bit values, independent of the local database.
Use persistent title/chapter/episode references rather than temporary stream URLs.
Do not put page numbers, selected quality or expiring tokens into a title identity.

Return accurate episode/chapter numbers, publication timestamps in epoch
**milliseconds**, state and available metadata. An unknown timestamp remains
unknown/zero; never replace it with the fetch time. A batch discovered today is not
a batch published today. Page list order is the source's published reading order;
reader direction and double-page display belong to Nyanime.

Verified external IDs can be supplied through `nyanime.tracking.v1` and optional
manga `SMangaTrackingMetadata`. Include only IDs proven to match the same edition
and season. Aliases are hints, not proof. The synthetic demo deliberately supplies
no real catalogue IDs. See [tracking metadata](https://github.com/owouwuiwi/nyanime/blob/main/docs/extension-tracking-metadata.md).

The optional manga `ReleaseScheduleProvider` contract can supply source-declared
future chapter releases. Use their typed SDK models, real
source dates and stated availability. Do not fabricate a schedule or require a
tracker login for basic source playback. Host notifications, follow state,
tracking, AniSkip and personal progress remain host responsibilities.

## Video adapter

The normal path is list → details/episodes → selected episode → hoster → video.

| Method | Input → output | Implementation rule |
| --- | --- | --- |
| `getFilterList()` | Fresh `AnimeFilterList` | New stateful filters for each call |
| `getPopularAnime(page)` | One-based page → `AnimesPage` | Stable title references; accurate `hasNextPage` |
| `getLatestUpdates(page)` | One-based page → `AnimesPage` | Advertise `supportsLatest` only when implemented |
| `getSearchAnime(page, query, filters)` | Query/filter snapshot → `AnimesPage` | Keep query and filters on every page |
| `getAnimeEpisodeUpdate(anime, episodes, fetchDetails, fetchEpisodes)` | Existing state/flags → `SAnimeEpisodeUpdate` | Preserve unrequested state; fetch requested changes |
| `getAnimeSeasonUpdate(anime, seasons, fetchDetails, fetchSeasons)` | Existing state/flags → `SAnimeSeasonUpdate` | Return verified season relations only |
| `getHosterList(episode)` | `SEpisode` → `List<Hoster>` | Preferred hoster first |
| `getVideoList(hoster)` | `Hoster` → `List<Video>` | Resolve playable URLs, qualities, tracks and required headers |

This complete override belongs **inside the existing `VideoSource`**; its `site`,
`asAnime()` and `episode()` helpers are defined in that source file:

```kotlin
override suspend fun getAnimeEpisodeUpdate(
    anime: SAnime,
    episodes: List<SEpisode>,
    fetchDetails: Boolean,
    fetchEpisodes: Boolean,
): SAnimeEpisodeUpdate {
    if (!fetchDetails && !fetchEpisodes) {
        return SAnimeEpisodeUpdate(anime, episodes)
    }
    val details = site.details(anime.url)
    return SAnimeEpisodeUpdate(
        if (fetchDetails) asAnime(details.entry) else anime,
        if (fetchEpisodes) details.parts.map(::episode) else episodes,
    )
}
```

`SAnime` carries title, stable URL, cover, background, description, genres and
status. `SEpisode` carries URL, name, numeric episode number and publication time.
The mapping helpers show their exact assignments. Use `initialized = true` only
when supplying the intended complete details; do not claim a title is completed
merely because its currently available episodes ended.

`VideoSource.kt` implements the public suspend API. `getAnimeEpisodeUpdate` shares
one extraction when details and episodes are requested together, and does no
network work when both flags are false. Season discovery returns none because the
demo publishes no season relations. A real adapter returns only verified relations.

Episode → hoster → video are distinct steps. The demo parses `<source>` quality
variants and `<track>` subtitles from its own HTML. Supply `Video.headers` only
when required. Subtitle/audio `Track` models carry a URL and language, not a
separate headers field. Never leak credentials to another origin.
Do not fetch or initialize the native player yourself. Source
references let the host handle sharing, Cast and rooms through generic contracts.

`Video.resolution` is vertical pixels, such as 360. `initialized = true` describes
an already resolved stream. A video-page iframe still needs extension-owned
resolution; iframe HTML is not a playable video. Older detail/list hooks remain
in the starter for compatibility; new logic should use the combined suspend API.

## Manga adapter

| Method | Input → output | Implementation rule |
| --- | --- | --- |
| `getFilterList()` | Fresh `FilterList` | Labels match declared Home controls |
| `getPopularManga(page)` / `getLatestUpdates(page)` | One-based page → `MangasPage` | Stable references and correct `hasNextPage` |
| `getSearchManga(page, query, filters)` | Query/filter snapshot → `MangasPage` | Apply supported filters on every page |
| `getMangaUpdate(manga, chapters, fetchDetails, fetchChapters)` | Existing state/flags → `SMangaUpdate` | Share a fetch; retain unrequested state |
| `getPageList(chapter)` | `SChapter` → `List<Page>` | Zero-based indices in original page sequence |

For direct final image URLs, this override belongs inside `MangaSource`:

```kotlin
override suspend fun getPageList(chapter: SChapter): List<Page> =
    site.pages(chapter.url).mapIndexed { index, url ->
        Page(index, imageUrl = url)
    }
```

`SManga` describes the title; `SChapter` its chapter URL, name, number and date.
The demo returns chapters newest first; the host owns the user's display order.
**Image pages stay in published reading sequence.** Never reverse, pre-pair or
drop pages for double-page display: that belongs to the reader.

`MangaSource.kt` implements public suspend methods and coherent legacy HTTP/Rx
hooks, including query, filters and page state. `getMangaUpdate` combines extraction.
Page models hold final image URLs, so `imageUrlParse` is not needed for this site.
If a site publishes intermediate image pages, implement that hook instead of
guessing a final URL. The demo includes a five-page chapter to exercise odd totals.

When adapting, keep both suspend methods and legacy HTTP/parse hooks coherent:
`popularMangaRequest/Parse`, `searchMangaRequest/Parse` and detail/chapter/page
hooks must not retain demo routes. For intermediate image pages, set `Page.url`
and implement `imageUrlParse`; for final images, set `Page.imageUrl` as above.

## News adapter

| Method | Input → output | Implementation rule |
| --- | --- | --- |
| `feed(request)` | `NewsRequest` → `NewsPage` | Apply cursor, medium and category |
| `search(query, request)` | Text/request → `NewsPage` | Implement when `capabilities.search` is true |
| `article(article)` | Summary → complete `NewsArticle` | Retain identity; return the real article body |

`NewsPage.nextCursor = null` ends pagination. Cursors are opaque to the host;
the demo happens to use numeric offsets. The source's identity comes through
its APK/factory: this API has no `NewsSource.id` property. `capabilities.media`
and `categories` declare available filters.

Native block kinds are `TEXT`, `HEADING`, `IMAGE`, `MEDIA` and `QUOTE`. Text uses
sanitized Markdown, not executable HTML. Unknown publication time is `null`.
Preserve publisher, author and attribution when provided.

Use the host-supplied `NewsHttpClient`, cursor pagination and declared media/category
capabilities. Return stable article IDs, publication dates, attribution and native
`NewsBlock` content. Excerpts are not full text. Declare `fullText` only when returning
the article body. Verified topic identities belong to the extension; do not attach
an unrelated title merely because two strings look similar. Preserve cancelled
requests and surface partial failures without substituting another article.

## TV adapter

| Method | Input → output | Implementation rule |
| --- | --- | --- |
| `catalogue(request)` | Country/language/category/cursor → `TvCatalogue` | Metadata only, no mass stream probes |
| `channels(references)` | Opaque references → `TvChannelLookup` | Optional `channelLookup`; distinguish unavailable from failed |
| `programmes(request)` | Channels/UTC interval → `TvGuide` | Distinguish missing guide, empty interval and failed request |
| `resolve(channel)` | `TvChannelRef` → `TvPlayback` | Resolve the selected channel's playable alternatives |

`TvCatalogue.nextCursor = null` ends pagination. Optional `options` returns
discovered facets; `TvHomeSection` declares channel sections. TV uses its typed
capabilities/sections, not the video/manga Home JSON. `TvChannelRef(sourceId, id)`
is opaque to Nyanime.

`TvStream` carries URL, headers, resolution, tracks, MIME type and declared
capabilities. Programme times and `TvClock.utcMillis` use epoch milliseconds;
`TvClock.mediaPositionSeconds` uses seconds. Only supply a clock when that mapping
is verified. The two-hour test signal is intentionally black and finite.

Channels and feeds use opaque `TvChannelRef` values. Return alternative streams of
the same feed together; keep regional/time-shifted feeds distinguishable. Declare
guide, channel lookup, rewind, speed and time-reference capabilities honestly.
Programme times use the TV API's UTC model. Missing guide is distinct from an
empty programme interval, stale data or a failed request.

The demo declares no guide, no rewind and no shared live clock. Its finite original
test signal exercises loading without pretending to be a broadcaster. Do not create
fake anime episodes to enter the player. The host owns live controls, PiP, Cast,
room negotiation and local buffering. See [TV API](https://github.com/owouwuiwi/nyanime/tree/main/tv-api).

## Addons, guides and settings

These optional families are not bundled into the four source examples:

* **RIN addons:** schema 2, `medium: addon`, `RinAddon` from `addon-api`.
  The host supplies `RinAddonHost` and `RinAddonContext`; use only declared
  UI/task capabilities. Release views and work on cancellation. An APK addon is
  a separate intent/PendingIntent protocol; it is not interchangeable with RIN.
* **Episode guides:** schema 2, `medium: guide`, `RinEpisodeGuideProvider`.
  Search receives public work identity; guide references resolve episode
  classifications. Unknown classifications remain unknown; no private progress
  or stream credentials are required. See [guide contract](https://github.com/owouwuiwi/nyanime/blob/main/docs/episode-guides.md).
* **Source preferences:** use `ConfigurableAnimeSource` / `ConfigurableSource`
  when the adapter actually needs settings. Store only source-owned values;
  avoid requesting credentials for publicly available fixtures.

For optional interfaces not exercised by the demo, inspect the exported matching
API sources before implementing. Declaring a capability without implementing it
does not make it supported.

## Network, cache and failure handling

The demo restricts URLs to its own HTTPS `/example/` area and rejects path escapes,
credentials and query strings. That is this adapter's policy, not a hardcoded
Nyanime limitation. Adapters needing signed query strings or other media origins
must adapt and test `SiteAddress` explicitly. Changing only `baseUrl` is not enough;
do not fix this by accepting arbitrary URLs or disabling certificate validation.

Video/manga share the host client, a bounded timeout, cancellable calls and a
1 MiB response limit. A per-source Mutex coalesces concurrent catalogue fetches
for 60 seconds. Failed responses are not cached. No app-wide client, crawler,
background refresh loop or eager video scan is created. News/TV use supplied HTTP
contracts. Rethrow cancellation; do not hide errors behind endless retries.

Handle no results, removed items, changed markup, missing images, unavailable
streams, malformed dates and offline errors explicitly. Never log tokens/cookies,
put credentials in shared links, or replace missing data with plausible guesses.

## Signing and updates

Build the selected examples before packaging. When changing the shared parser,
build all four:

```sh
python -m unittest discover -s tests -v
./gradlew :common:test :video:assembleDebug :manga:assembleDebug :news:assembleRelease :tv:assembleDebug
```

For local video development, create/reuse a private identity and verify the RIN:

```sh
python tools/pack.py video --development
python tools/verify_rin.py dist/placeholder-video-1.0.0.rin
```

Replace `video` with `manga` or `tv` to package another built example. The filename
uses `template.json.versionName`; adjust it when changing that value. Outputs and
public verification reports appear in `dist/`. The packer extracts DEX/assets from
the build container and signs the RIN independently of Android debug signing.
Your development key/certificate are created once in `.local/`: **back them up
privately and never commit them**. For distribution, use your own retained identity:

RIN contains `classes.dex`, optional secondary DEX, `assets/`, `manifest.json`,
`META-INF/rin.cert` and `META-INF/rin.sig`. The signature covers the **exact manifest
bytes**; its hash map covers every payload file. Use RSA-SHA256 or ECDSA-SHA256 and
an X.509 DER certificate. The starter creates a local development RSA identity.

```sh
python tools/pack.py video --key /private/publisher.pem --certificate /private/publisher.der
python tools/verify_rin.py dist/placeholder-video-1.0.0.rin
```

Keep the private key out of source, CI logs and website downloads. Reusing another
publisher's package/source IDs or replacing a lost key is not a valid update.
The host checks integrity, supported API, package, source IDs, signer and increasing
versions before activation. Same-version changed bytes and downgrades are refused.
Local import displays the certificate fingerprint for explicit approval; a valid
signature alone is not a claim of publisher reputation.

Current RIN limits include 32 MiB, 512 ZIP entries and 64 KiB manifest. News APKs
use normal Android APK signing; development debug signatures must be replaced for
public distribution. Build `:news:assembleRelease`, then run:

```sh
python tools/sign_apk.py --build-tools /path/to/android-sdk/build-tools/35.0.1 --key /private/publisher.pem --certificate /private/publisher.der
```

This rejects debuggable APKs, checks implementation classes, aligns the archive
and verifies the resulting signature. `--development` replaces the two key
arguments to reuse the local demo identity. Keep `JAVA_HOME` set: `apksigner`
needs Java too. Native API namespace strings remain compatibility identifiers.

The optional `assets/nyanime/extension-v1.json` declares distribution identity and
manual/repository update policy. This starter uses manual updates and has no
embedded catalogue. A separately maintained public catalogue is optional; never
bundle its addresses or private signing material into the host.

## Install and check the result

Use Nyanime supporting standalone RIN import, **version code 232+**, with the
pinned APIs. Open **Store → Load RIN**, choose the video/manga/TV file, review the
publisher fingerprint and explicitly approve it. Enable English sources if hidden.
No catalogue registration is required for local import.

For local News development, build `:news:assembleDebug` and install
`news/build/outputs/apk/debug/news-debug.apk`. Public distribution uses the signed
non-debug APK described above. Approve the source in Nyanime and select it in News.
Never install both APK and RIN copies of the same source or rename APKs to RINs.

| Example | Expected result |
| --- | --- |
| Video | Selectable DEMO Animation / DEMO Cartoons Homes; scoped sections and filters; title → episode → qualities/subtitles |
| Manga | DEMO Manga Home; title → chapter → original page order, including the odd-page chapter |
| News | Paged feed, search/media filters and full native articles |
| TV | Synthetic channel plays its finite black test file; guide explicitly unavailable |

Home categories can be enabled/reordered in the user's settings. They disappear
when the last enabled contributing extension is removed. Their IDs must not
become title identities or duplicate library entries.

## Troubleshooting

| Symptom | Check first |
| --- | --- |
| Java/Gradle setup fails | `JAVA_HOME` points to JDK 17; the specified platform and Build Tools are installed |
| Another website shows demos or fails parsing | Adapt request routes, selectors, mapping and URL policy, not just `baseUrl` |
| RIN import is rejected | Run `verify_rin.py`; check API floor, payload, DEX dependencies, signer and version |
| Source missing | Correct family/format, explicit trust approval, language/visibility, no duplicate APK/RIN |
| Home missing or wrong content | Source name/language match, category enabled, IDs and filter labels/defaults correct |
| Home JSON edits disappear | Update `configure.py`; it overwrites generated declarations |
| Filters work only on page one | Retain query/filter/date state and calculate next-page state from filtered results |
| Directory appears twice in links | HTTP source `baseUrl` is origin; stored references include the website directory |
| Demo video is black and silent | Intentional; test seeking, both qualities and English subtitles |
| No TV schedule | Intentional: the finite fixture advertises no guide or live clock |
| Update refused | Same package, source IDs and signer; strictly higher `versionCode` |

## Release checklist

- [ ] Choose unique stable package/source IDs; replace demo labels and identities.
- [ ] Review URLs, selectors, timestamps, capabilities and model fields.
- [ ] Pin a matching compile-only SDK and retain licences/attribution.
- [ ] Run tool/parser tests and build the selected modules.
- [ ] Cover empty results, filtered pagination, malformed data, cancellation and failures.
- [ ] Keep persistent references, original page order and honest unknown dates.
- [ ] Verify payload hashes, signature and public publisher fingerprint.
- [ ] On a physical device, test explicit approval, first import and a higher-version update.
- [ ] Check Home categories, sections, filters, search and final-page exhaustion.
- [ ] Test details, qualities/subtitles or every chapter page, odd totals, rotation and progress.
- [ ] Check News body/TV missing-guide states when using those families.
- [ ] Test slow/offline behavior, retry, source disable/removal and missing-source messages.
- [ ] Check narrow layouts, large text, light/dark themes and reduced motion.
- [ ] Verify room/Cast/PiP paths separately if supported; do not infer from local playback.
- [ ] Exclude keys, credentials and machine paths from Git and downloads.
- [ ] Increase the version, retain signing identity and publish reproducible instructions.
- [ ] Confirm rights to distributed content/metadata; a code licence grants no media rights.

## Build, tests and reproducibility

Run the Python tool tests and `:common:test` before packaging. Parser tests operate
on the original website fixtures and cover pagination, filters, scoped Home data,
identity, page order, URL boundaries, shared requests and failure recovery.
Python tests cover configuration, signatures and tampering. Packaging verifies
payload hashes and emits a public fingerprint/SHA-256 report beside the RIN.

`tools/generate_site.py --ffmpeg /path/to/ffmpeg` regenerates original images,
HTML/JSON, VTT subtitles and synthetic videos. It needs Pillow and FFmpeg only for
fixture regeneration, not extension compilation or normal use. Existing videos
are reused. `website/assets-manifest.json` records published fixture hashes.

To regenerate the fixture website and this same guide, install the optional site
dependencies. FFmpeg is required only when generating the synthetic clips:

```sh
python -m pip install -r requirements-site.txt
python tools/generate_site.py --ffmpeg /path/to/ffmpeg
python tools/render_guides.py
python tools/package_kit.py
```

`render_guides.py` renders this guide for the website; GitHub and the downloaded
kit use the same Markdown. `package_kit.py` includes source, SDK and fixtures,
excluding keys and build directories. Original demo media/text use CC0-1.0;
extension code uses Apache-2.0. Branding and fonts retain their own notices;
see [media credits](../website/ASSETS.md) and `NOTICE`.

Use the [release checklist](#release-checklist) for physical-device verification.
Compilation and signatures do not prove Home, reader, player or trust UI behavior.
Record host version and device separately from build results. Add site-specific
parser fixtures/tests in the extension repository; the host stays generic.
