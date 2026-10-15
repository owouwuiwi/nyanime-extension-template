# Build a Nyanime extension

Build, sign and test an extension without changing Nyanime. Choose the path
that matches your experience; both lead to the same complete guide.

<nav class="guide-entry-points" aria-label="Choose your starting point">
<a href="#for-existing-extension-authors"><strong>I already build extensions</strong><span>Keep your AniYomi/Mihon source. Check its ABI, then add only what you need. →</span></a>
<a href="#set-up-and-build-the-unchanged-example"><strong>This is my first extension</strong><span>Set up, build an original example, sign it and try Install or Import. →</span></a>
</nav>

The examples use original geometric drawings, sample articles and intentionally
black, silent videos from [the playground](https://owouwuiwi.github.io/example/).
**Nyanime does not promote piracy in any way or form.** Bring your own content and
use only material you are legally entitled to access.
[Read our position](https://owouwuiwi.github.io/responsible-use/).

This is the canonical guide for the starter, website and downloadable kit.
New releases are **one publisher-signed APK**: install it through Android or import
it privately into a supporting Nyanime version. Neither mode requires a catalogue.
All six families share the same inventory, verification and management flow.

**Compatibility has a scope.** The video APK was tested on AniYomi 0.18.2.1 and
the manga APK on Mihon 0.21.2, as well as Nyanime. Other families need a host that
implements their own contracts. See the exact artifacts and runtime limits in
[VERIFICATION.md](../VERIFICATION.md). An API number alone is not proof of ABI
compatibility.

The [upstream profile lock](../sdk/portable-sdk-lock.json) pins independent base
APIs. The [Nyanime SDK lock](../sdk/sdk-lock.json) records the optional host export,
source hashes and compile-only JAR hashes. They serve different purposes; do not
replace your base API with a host-specific export just to enable private import.

## For existing extension authors

You do not need to rewrite a working AniYomi/Mihon extension or publish a second
format. First test your existing **signed release APK** in Nyanime. If its base
family and ABI are supported, both installation modes can use those same bytes.
Keep your package, publisher certificate, source IDs, normal discovery metadata
and update versioning stable.

| Keep as it is | Add only if your extension needs it |
| --- | --- |
| Your parser, requests, URLs, filters and pagination | Declarative Home categories/sections in `assets/aniyomi/home-v1.json` |
| Base factory and upstream method/field signatures | A separately declared optional Nyanime factory for code capabilities |
| Package, source IDs and retained publisher key | Matching signed distribution metadata for an explicit update origin/policy |
| Compile-only host/shared dependencies | Rich metadata through a supported optional contract |
| One signed APK for compatible hosts | Tests for every host/version and mode you actually claim |

### The shortest useful path

1. **Keep your identity.** Retain the package, source IDs, publisher key, normal discovery metadata and base factory; changing installation mode does not require a rewrite.
2. **Check the real compiled ABI.** Use the applicable pinned profile below, replacing the classes path with your release output. For a different target, pin its actual upstream profile rather than lowering Nyanime's APIs.
3. **Build and sign your existing release APK.** Bundle your implementation only; host/shared libraries remain `compileOnly`. Use the same signed bytes for Install and Import.
4. **Test both modes and the foreign host you claim.** Verify explicit approval, identity, search, details, actual playback/reading and a higher-version update. A catalogue is optional.
5. **Add integration only where needed.** Start with the [declarative Home contract](#home-categories-sections-and-filters). Isolate Nyanime-only code from the base factory as shown below.

Run the check for your family, from the starter root:

```sh
python tools/check_abi.py --profile aniyomi-video-api --classes video/build/tmp/kotlin-classes/release
python tools/check_abi.py --profile aniyomi-manga-api --classes manga/build/tmp/kotlin-classes/release
```

| Family | Pinned compile-only profile | Verified scope / requirement |
| --- | --- | --- |
| Video | `aniyomi-video-api`, anime API 17 | Same APK tested on AniYomi 0.18.2.1; Nyanime paths are recorded in the verification report |
| Manga | `aniyomi-manga-api`, common manga API 1.4 | Same APK tested on Mihon 0.21.2; Nyanime paths are recorded in the verification report |
| News | Exported `news-api.jar`, API 1 | Needs the news contract; no AniYomi/Mihon compatibility claim |
| TV | Exported `tv-api.jar`, API 1 | Needs the TV contract; the fixture has no real live clock or guide |
| Guide | Exported `addon-api.jar`, guide API 1 | Needs `EpisodeGuideProvider`; the fixture returns honest empty results |
| Hosted addon | Exported `addon-api.jar` | Needs `HostedAddon`; registered Android components require Install |

### Isolate optional capabilities

Keep the portable factory in your base namespace. Put the optional factory in a
**separate compilation unit/namespace**, compiled against the matching Nyanime
SDK. The smallest valid attachment demonstrates the boundary without claiming a
feature it does not implement:

```kotlin
package example.publisher.optional

import nyanime.extension.api.SourceCapabilitiesFactory

class PresentationFactory : SourceCapabilitiesFactory {
    override fun attach(sources: List<Any>): List<Any> = sources
}
```

Declare it in the APK application's metadata:

```xml
<meta-data
    android:name="nyanime.optional.factory"
    android:value="example.publisher.optional.PresentationFactory" />
```

This passthrough adds no behavior. Implement and test an actual optional contract
inside that isolated unit when needed. The base source/factory must **not** import,
construct, inherit from, or expose host-only classes in its method signatures.
Nyanime calls `attach` after loading trusted base sources; preserve their ordered
medium/source identities. A failed optional attachment leaves the base usable.
Other hosts ignore this optional metadata and must be able to load the base alone.

When checking combined class output, `--optional-prefix example/publisher/optional/`
may exclude only that isolated unit from the **upstream** ABI check. Do not exclude
your base factory or parser. Check the optional unit against the Nyanime profile,
retain `compileOnly` dependencies and test the final DEX/package as well.

Continue with [signing and updates](#signing-and-updates) and the
[real-device checklist](#release-checklist). The sections below explain each
contract in detail without requiring a source rewrite.

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

Extensions execute code in the host process after approval. **An APK extension contains signed
executable code; it is not a security sandbox.** Never request unrelated permissions,
inspect host databases, depend on private host classes or run permanent services.
Use public APIs and cancellation-aware network calls. Approval is explicit;
installation must never silently trust a publisher.

Shared APIs and libraries are `compileOnly`. Bundle your implementation only.
`sign_apk.py` inspects DEX class definitions and rejects accidentally bundled host,
Kotlin, networking or parsing libraries. Keep the default implementation namespace
while learning; if changing it, update the packer's allowed namespace too.

The host SDK export includes source-api, core-common, news-api, tv-api and addon-api.
Base video/manga modules compile against separately pinned upstream profiles;
see the [existing-author path](#for-existing-extension-authors) and [profile lock](../sdk/portable-sdk-lock.json).
Each module uses only the contracts it needs. Keep SDK dependencies aligned with
the target host; do not confuse an extension build library with the runtime API.

## Choosing a family

| Family | Entry point | Public operations | Current starter distribution |
| --- | --- | --- | --- |
| Video | `AnimeSourceFactory` → `AnimeHttpSource` | Popular/latest/search, details, episodes, seasons, hosters, videos | Signed APK, anime API 17 |
| Manga | `SourceFactory` → `HttpSource` | Popular/latest/search, details, chapters, pages, image loading | Signed APK, common manga API 1.4 |
| News | `NewsSourceFactory.create(NewsHttpClient)` | Feed, optional search, complete article | APK, News API 1 |
| TV | `TvSourceFactory.create(http, cache)` | Catalogue, channel lookup, guide, playback resolution | Signed APK, TV API 1 |
| Guide | `EpisodeGuideProvider` | Work search, episode classification | Signed APK, guide API 1 |
| Addon | `HostedAddon` | Component-free UI and declared tasks | Signed APK, hosted addon API 1 |

These are independent source families, not mandatory dependencies. The guide
and addon modules demonstrate separate, component-free contracts: they do not
pretend to be video sources. Every new output is a signed APK. Legacy `.rin`
files can still be imported and restored; no forced migration is required.
Renaming a `.rin` file to `.apk` (or the reverse) does not convert it.

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

**First extension? Start here.** Complete the unchanged synthetic example before
adapting a website. No catalogue, Nyanime account or paid developer service is
needed. An initial SDK/dependency download can take time; this is not a promise
of an instant first build.

### 1. Prepare your tools

Use **Use this template** on the [starter repository](https://github.com/owouwuiwi/nyanime-extension-template),
clone it, or extract the [complete kit](https://owouwuiwi.github.io/example/downloads/v1.0.2/placeholder-extension-kit.zip).
Open a terminal in the directory containing `template.json` and `gradlew`.

For the verified import flow, use **Nyanime 0.45.0.1 (build 238) or newer**.
The package contract floor and the versions tested are distinct; consult the
verification report before claiming an older combination.

Install **JDK 17**, **Android SDK platform 36 / Build Tools 35.0.1** and
**Python 3.10+**. Set `JAVA_HOME` to the JDK directory. Set `ANDROID_HOME` to
the SDK directory, or create `local.properties` with `sdk.dir=/your/android/sdk`.
Android Studio's SDK Manager can install the specified platform and tools.
On Windows, replace `./gradlew` with `./gradlew.bat` in every command below.

### 2. Build one original example

The commands below choose video. For manga, replace `video` with `manga` in both
the Gradle task and signing command. Keep the demo configuration for this first
local test; choose your own stable identity before publishing.

```sh
python -m pip install -r requirements-tools.txt
python tools/configure.py
python -m unittest discover -s tests -v
./gradlew :common:test :video:assembleRelease
```

On Windows PowerShell, the Gradle command is:

```powershell
.\gradlew.bat :common:test :video:assembleRelease
```

This tests the parser and creates `video/build/outputs/apk/release/video-release-unsigned.apk`.
Sign it before installation. For every family, the signed release APK is the
distributable artifact. Keep the public demo URL unchanged
for the first build; another website requires another parser.

### 3. Sign, then try the same APK

For the unchanged local demo, use the helper's persistent development identity.
Replace the Build Tools path with the directory installed on your computer:

```sh
python tools/sign_apk.py video --development --build-tools /path/to/android-sdk/build-tools/35.0.1
```

On Windows, a typical path can contain spaces; quote it:

```powershell
python tools/sign_apk.py video --development --build-tools "C:/path/to/Android/Sdk/build-tools/35.0.1"
```

The file is `dist/placeholder-video-1.0.1.apk` with this starter configuration.
The helper creates/reuses its owned demo identity under ignored `.local/`, not
Android's shared debug key. Keep the identity if you want to test updates. Do not
commit it or include it in a download. For your public extension, use and back up
your own publisher key/certificate as explained under [signing](#signing-and-updates).

Choose either route; neither is the required default:

| Install | Import |
| --- | --- |
| Open the signed APK with Android, complete installation, then approve the publisher in Nyanime. Compatible hosts can discover the Android package too. | In Nyanime, open **Store → Import extension**, choose the APK and approve its verified publisher. The executable copy stays private to Nyanime. |
| Android manages the installed package. | No Android installation is required for a component-free extension. |

Both routes run extension code with the host's permissions after approval.
Approve only a publisher you trust. For these manually distributed demos,
**Manual updates · no catalogue associated** is expected. Automatic updates need
an explicitly associated compatible origin; importing a file does not invent one.

### 4. Check it, then make it yours

Enable the example's English source if hidden. Open its demo Home, a title and
an episode/chapter. A black silent video is intentional; seek and try subtitles.
The manga example must display the actual original pages in order.

Next, [configure your own identity](#configure-identity-and-discovery), adapt the
parser, and follow the family-specific section. Before calling it supported,
complete the [release checklist](#release-checklist). A successful compilation is
not a device test. The [glossary](#glossary) explains the terms used below.

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
| `minimumHostVersionCode` | Compatible host floor; at least `237` for this starter's interoperable APK import path |

The same module fields exist for manga, news, TV, guide and addon. Keep all six declarations
even when building one module. Never distribute your own product with demo IDs.

`configure.py` generates Android manifests, icons, distribution metadata and
video/manga Home JSON. **It overwrites those generated files.** For lasting custom
Home declarations, change its `home()` generator, not only the generated JSON.

The configured package identity is separate from the Kotlin namespace
`example.placeholder.*`, which you can keep while learning. If renaming Kotlin
packages, also update factory names in `configure.py` and the APK signing helper, Gradle
namespaces and the packer's DEX allowlist. The configuration does not rename code.

The host discovers factories through metadata: Android class/factory metadata and the optional signed package declaration.
`configure.py` registers these for
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

See the authoritative [Home contract](https://github.com/owouwuiwi/nyanime/blob/v0.45.0.1/docs/extension-home-api.md)
and [manga Home additions](https://github.com/owouwuiwi/nyanime/blob/v0.45.0.1/docs/manga-home-api.md).

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
no real catalogue IDs. See [tracking metadata](https://github.com/owouwuiwi/nyanime/blob/v0.45.0.1/docs/extension-tracking-metadata.md).

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
| `getAnimeDetails(anime)` | Stable title reference → `SAnime` | Return real details from that title |
| `getEpisodeList(anime)` | `SAnime` → `List<SEpisode>` | Keep stable references, numbers and publication times |
| `getSeasonList(anime)` | `SAnime` → `List<SAnime>` | Verified relations only; empty for this synthetic fixture |
| `getHosterList(episode)` | `SEpisode` → `List<Hoster>` | Preferred hoster first |
| `getVideoList(hoster)` | `Hoster` → `List<Video>` | Resolve playable URLs, qualities, tracks and required headers |

This override belongs **inside the existing `VideoSource`**. Its `site` and
`episode()` helpers are defined in that source file and link against the pinned
upstream video profile:

```kotlin
override suspend fun getEpisodeList(anime: SAnime): List<SEpisode> =
    site.details(anime.url).parts.map(::episode)
```

`SAnime` carries title, stable URL, cover, background, description, genres and
status. `SEpisode` carries URL, name, numeric episode number and publication time.
The mapping helpers show their exact assignments. Use `initialized = true` only
when supplying the intended complete details; do not claim a title is completed
merely because its currently available episodes ended.

`VideoSource.kt` implements the upstream anime API 17 suspend entry points and
coherent legacy HTTP hooks. It does not depend on Nyanime-only combined-update
models. The optional host SDK also exposes richer update contracts; keep those
outside the portable base when using them. Season discovery returns none because
the demo publishes no season relations. A real adapter returns only verified ones.

Episode → hoster → video are distinct steps. The demo parses `<source>` quality
variants and `<track>` subtitles from its own HTML. Supply `Video.headers` only
when required. Subtitle/audio `Track` models carry a URL and language, not a
separate headers field. Never leak credentials to another origin.
Do not fetch or initialize the native player yourself. Source
references let the host handle sharing, Cast and rooms through generic contracts.

`Video.resolution` is vertical pixels, such as 360. `initialized = true` describes
an already resolved stream. A video-page iframe still needs extension-owned
resolution; iframe HTML is not a playable video. Keep the entry points required by the chosen base profile. Do not copy a
host-only combined-update signature into an upstream factory to enable import.

## Manga adapter

The portable example targets the pinned **manga API 1.4 HTTP/Rx profile**. These
are its implemented hooks; host-specific suspend/combined-update interfaces are
not required for its base to load on Mihon.

| Hook | Input → output | Implementation rule |
| --- | --- | --- |
| `getFilterList()` | Fresh `FilterList` | Labels match declared Home controls |
| `popularMangaRequest/Parse` / `latestUpdatesRequest/Parse` | One-based page ↔ request/response → `MangasPage` | Stable references and correct `hasNextPage` |
| `searchMangaRequest/Parse` | Query/filter snapshot ↔ request/response → `MangasPage` | Apply query and filters on every page |
| `mangaDetailsRequest/Parse` | `SManga` ↔ response → `SManga` | Return actual details for the same identity |
| `chapterListRequest/Parse` | `SManga` ↔ response → `List<SChapter>` | Stable chapter references and publication metadata |
| `pageListRequest/Parse` | `SChapter` ↔ response → `List<Page>` | Zero-based indices in original page sequence |

For final image URLs, this override belongs inside the existing `MangaSource`.
`Response`, `SiteParser` and `address` already come from that file:

```kotlin
override fun pageListParse(response: Response): List<Page> =
    response.use {
        SiteParser.pages(it.body.string(), address).mapIndexed { index, url ->
            Page(index, imageUrl = url)
        }
    }
```

`SManga` describes the title; `SChapter` its URL, name, number and date. The demo
returns chapters newest first; the host owns the user's display order.
**Image pages stay in published reading sequence.** Never reverse, pre-pair or
drop pages for double-page display: that belongs to the reader. The demo includes
a five-page chapter to exercise odd totals.

Keep each request/parse pair coherent when adapting a site. For intermediate
image pages, set `Page.url` and implement `imageUrlParse`; for final images, set
`Page.imageUrl` as above. The demo never needs a second image-page lookup.

Nyanime's optional manga API 1.6 `getMangaUpdate` / `SMangaUpdate` contract can
combine requests and preserve unrequested state, but this base example does not
implement or reference it. Neither that contract nor `SMangaHomeMetadata`,
`SMangaTrackingMetadata` or `ReleaseScheduleProvider` should leak into a factory
that must load on a host providing only the common 1.4 profile. Use a separate
optional attachment or an explicitly different tested target profile.

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
room negotiation and local buffering. See [TV API](https://github.com/owouwuiwi/nyanime/tree/v0.45.0.1/tv-api).

## Addons, guides and settings

Guide and addon have independent modules and compile-only contracts. Their
small examples verify loading and UI without inventing real guide data or
starting permanent services: [guide](../guide/src/main/kotlin/example/placeholder/guide/GuideFactory.kt),
[addon](../addon/src/main/kotlin/example/placeholder/addon/AddonFactory.kt).

* **Hosted addons:** component-free signed APKs, `medium: addon`, `HostedAddon` from `addon-api` (legacy `RinAddon` ABI retained).
  The host supplies `RinAddonHost` and `RinAddonContext`; use only declared
  UI/task capabilities. Release views and work on cancellation. An addon using
  registered Android components follows the intent/PendingIntent protocol and
  declares `nyanime.extension.requires_android=true`; it supports Install only.
  An APK is a package format, not a statement that it needs Android components.
* **Episode guides:** schema 2, `medium: guide`, `EpisodeGuideProvider` (legacy `RinEpisodeGuideProvider` ABI retained).
  Search receives public work identity; guide references resolve episode
  classifications. Unknown classifications remain unknown; no private progress
  or stream credentials are required. See [guide contract](https://github.com/owouwuiwi/nyanime/blob/v0.45.0.1/docs/episode-guides.md).
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

Both adapters derive their network client from the host and use a bounded call
timeout. The video helper additionally enforces a 1 MiB response limit and uses
a per-source Mutex to coalesce catalogue fetches for 60 seconds; failures are
not cached. Manga keeps coherent HTTP/Rx request/parse hooks and closes responses.
These details are not a claim that every family has the same cache or size limit. No app-wide client, crawler,
background refresh loop or eager video scan is created. News/TV use supplied HTTP
contracts. Rethrow cancellation; do not hide errors behind endless retries.

Handle no results, removed items, changed markup, missing images, unavailable
streams, malformed dates and offline errors explicitly. Never log tokens/cookies,
put credentials in shared links, or replace missing data with plausible guesses.

## Signing and updates

Build the selected examples before packaging. When changing the shared parser,
build all six:

```sh
python -m unittest discover -s tests -v
./gradlew :common:test :video:assembleRelease :manga:assembleRelease :news:assembleRelease :tv:assembleRelease :guide:assembleRelease :addon:assembleRelease
```

For every module, build a release APK and sign it with the same retained
publisher identity. The signed bytes are used by both Android installation and
private import. Local demo signing also avoids Android's shared debug key:

```sh
python tools/sign_apk.py video --development --build-tools /sdk/build-tools/35.0.1
python tools/sign_apk.py manga --development --build-tools /sdk/build-tools/35.0.1
python tools/sign_apk.py news --development --build-tools /sdk/build-tools/35.0.1
python tools/sign_apk.py tv --development --build-tools /sdk/build-tools/35.0.1
python tools/sign_apk.py guide --development --build-tools /sdk/build-tools/35.0.1
python tools/sign_apk.py addon --development --build-tools /sdk/build-tools/35.0.1
```

For distribution, replace `--development` with your own `--key` and
`--certificate` paths. Preserve that key/certificate pair for updates. Signing
rejects debuggable APKs, checks implementation-only DEX, aligns the archive and
verifies the APK signature. Keep keys out of Git, CI logs and downloads.

APK signatures authenticate all executable and resource bytes. The optional
`assets/nyanime/package-v1.json` must agree with Android identity, version, API and
entry metadata. It does not replace Android signatures with a second envelope.
Do not create new RINs; `verify_rin.py` remains only for legacy compatibility.

Run the compiled base ABI checks in the [existing-author path](#for-existing-extension-authors)
before claiming another host is supported. A numeric API match and a successful
build alone are insufficient. Keep optional Nyanime classes separate from the
base source/factory and shared parsers.

The optional `assets/nyanime/extension-v1.json` declares distribution identity and
manual/repository update policy. This starter uses manual updates and has no
embedded catalogue. A separately maintained public catalogue is optional; never
bundle its addresses or private signing material into the host.

## Install and check the result

Nyanime's **Store** manages anime, manga, news, TV, guide and addon packages in
one inventory. **Install** and **Import** use the same publisher-signed APK:

* **Install:** Android manages the package, and other compatible hosts may discover
  it. A cancelled Android installation is not reported as a successful import.
* **Import:** Nyanime keeps a private immutable copy. Open **Store → Import
  extension** to choose a local APK, without adding a catalogue or choosing a
  storage directory. The preview shows identity, version and publisher fingerprint
  before execution is approved.
* **Android-component addon:** **Install** is the only option. The app explains:
  “This extension needs Android components. Use Install.” A component-free hosted
  addon or episode guide can use private import.

Choose the mode that fits your use. Enable English sources if hidden. Base API
namespaces, source identities and the underlying parser do not change with mode.
Legacy `.rin` files can still be imported/restored; no conversion is forced, and
renaming a file is not conversion. New starter tools publish APKs only.

### Approval is separate from discovery

A signature identifies the publisher; it does not prove that code is harmless.
Nyanime asks for individual approval. Adding a catalogue does not approve its
executables. An optional **Trust extensions from this catalogue** consent is
initially off, revocable, and covers only current/future extensions the user
chooses to add. It installs nothing automatically and grants no authority to
replace an unrelated publisher or uninstall an extension.

### Updates and update origins

Imported automatic updates start enabled, with a switch per extension. A worker with a network constraint checks on a six-hour interval; an overdue check at app opening
uses the same coordinator. **Android may defer work.** Do not promise an exact
time, a six-hour delivery deadline, or instant background updates.

An import without a known origin shows **Manual updates · no catalogue associated**.
The user can import a newer signed APK manually or choose **Associate an update
catalogue** explicitly. Only a configured catalogue offering the same package and
publisher can be associated. Origin association and execution consent are separate;
no official/preconfigured catalogue is included or required by the starter.

### Safe activation and mode changes

Download, integrity/signature verification and factory preflight happen before an
atomic active-version switch. The package must preserve its family and known
source IDs. Files are immutable. A failed/interrupted update keeps the previous
version available, and a disabled extension stays disabled.

Reading, playback, Cast and active addon tasks defer activation. Finish that work,
then retry rather than deleting the active package. The same approved publisher
can have Android and private copies: the newest compatible version is used;
equal versions retain the selected mode. A same-version mode change requires
identical APK bytes. Downgrades, changed same-version bytes and an unrelated
publisher cannot silently take over. A verified supported certificate rotation
is different from an unrelated new certificate.

| Example | Expected result |
| --- | --- |
| Video | Selectable DEMO Animation / DEMO Cartoons Homes; scoped sections and filters; title → episode → qualities/subtitles |
| Manga | DEMO Manga Home; title → chapter → original page order, including the odd-page chapter |
| News | Paged feed, search/media filters and full native articles |
| TV | Finite black synthetic signal; guide and shared live clock explicitly unavailable |
| Guide | Provider settings and honest no-results responses; no fabricated classifications |
| Hosted addon | Original hosted view and return to Nyanime; no permanent background service |

Home categories can be enabled/reordered in user settings. They disappear when
the last enabled contributor is removed. Their IDs must not become title
identities or duplicate library entries. See [VERIFICATION.md](../VERIFICATION.md)
for what was tested, with which artifacts and host versions.

## Troubleshooting

The quoted messages below come from Nyanime 0.45.0.1's English UI. A later host
may phrase them differently; check the error before changing identities or keys.

| Message / symptom | What it means | Next action |
| --- | --- | --- |
| “Manual updates · no catalogue associated” | The imported file has no associated update origin; this is not a failed import | Import a newer verified APK manually, or use **Associate an update catalogue** with a compatible configured origin |
| “No compatible catalogue is configured. You can still update by importing the file manually.” | Nothing configured can provide an update for that publisher/package | Keep manual updates, or configure and explicitly associate a compatible origin; do not invent a default catalogue |
| “This extension needs Android components. Use Install.” | Registered Android runtime components cannot be supplied by a private import | Use **Install**, or redesign the addon as genuinely component-free; renaming it cannot fix this |
| “This extension requires a different Nyanime version. Update the app or choose a compatible file.” | Family/API/host requirements are incompatible | Use a matching host/file and check actual compiled ABI; do not simply lower API numbers |
| “The extension could not be replaced. Check its publisher, version and source identities, then choose the file again. Your previous version is unchanged.” | Replacement validation did not preserve identity/version/publisher | Compare the fingerprint, stable IDs, package and strictly higher version; preserve the existing key. A changed publisher needs explicit review |
| “The file is not a valid signed extension or cannot be read. Choose an APK or a legacy .rin file.” | The file is unreadable, malformed, unsigned or not the claimed package | Re-download the original and verify its checksum/signature. Do not rename a legacy archive into an APK |
| “Close playback, reading and active addons before updating an extension.” | The old executable is still in use; Cast can also defer activation | Finish the active session and retry; leave the verified previous copy intact |
| “Update failed. The previous version remains available.” | Download, verification or activation failed | Check connectivity, artifact identity and logs, then retry; do not mark an unactivated version successful |
| Source missing | Family, discovery, consent, language, visibility or active mode may be wrong | Inspect **My extensions**, approve the intended publisher and enable the source language |
| Another website fails parsing | A URL change did not adapt the parser | Update request routes, selectors, mapping and URL policy inside the extension |
| Home missing / generated edits disappear | Source name/language, enabled category, IDs, labels or generator are inconsistent | Fix the declaration and `configure.py` generator, not a hardcoded host route |
| Filters work only on page one | Query/filter/date state was discarded | Carry it to every request and calculate `hasNext` from filtered results |
| `NoSuchMethodError` / `NoClassDefFoundError` in another host | Actual ABI differs, or optional/shared classes leaked into the base | Inspect compiled method/field descriptors, `compileOnly` packaging and the optional factory boundary; an API number is insufficient |
| Demo video black / TV guide missing | This fixture is intentionally synthetic | Test playback/seek/subtitles; do not invent content or guide entries |
| Java/Gradle fails | Tools or paths do not match the prerequisites | Check JDK 17, SDK platform 36, Build Tools 35.0.1 and `JAVA_HOME` |

## Glossary

| Term | Meaning here |
| --- | --- |
| Host | Nyanime or another app loading an extension through a supported contract |
| Family | Video, manga, news, TV, guide or addon; each has its own API |
| API / ABI profile | Public operations / the actual JVM class, method and field signatures a compiled extension must link against |
| `compileOnly` | Available while compiling, supplied by the host at runtime; not bundled again in the extension |
| Package / source ID | Stable extension identity / stable content-provider identity; neither is a title's local database row |
| Publisher fingerprint | Hash identifying the signing certificate; review it before approving execution |
| Install / Import | Android-managed package / private executable copy in Nyanime, from the same signed APK |
| Catalogue / origin | Optional discovery index / explicitly associated location allowed to supply this package's updates |
| Preflight / activation | Validate and load-check first / atomically select the verified immutable version afterward |
| Optional factory | Separate Nyanime-only attachment loaded after the portable base; not a new required superclass |

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
payload hashes and emits a public fingerprint/SHA-256 report beside the APK.

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
