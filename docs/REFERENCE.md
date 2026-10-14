# Nyanime extension reference

This reference accompanies the [quick start](../README.md). Examples target the
exported SDK in `sdk/sdk-lock.json`. That file records the host revision, source
hashes and API JAR hashes. It is not a promise that every old host supports every
new optional capability. Consult the linked contracts before publishing.

## Architecture and ownership

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

`VideoSource.kt` implements the public suspend API. `getAnimeEpisodeUpdate` shares
one extraction when details and episodes are requested together, and does no
network work when both flags are false. Season discovery returns none because the
demo publishes no season relations. A real adapter returns only verified relations.

Episode → hoster → video are distinct steps. The demo parses `<source>` quality
variants and `<track>` subtitles from its own HTML. Supply `Video.headers` and
track headers only when required for that resource; do not leak credentials to
another origin. Do not fetch or initialize the native player yourself. Source
references let the host handle sharing, Cast and rooms through generic contracts.

## Manga adapter

`MangaSource.kt` implements public suspend methods and coherent legacy HTTP/Rx
hooks, including query, filters and page state. `getMangaUpdate` combines extraction.
Page models hold final image URLs, so `imageUrlParse` is not needed for this site.
If a site publishes intermediate image pages, implement that hook instead of
guessing a final URL. The demo includes a five-page chapter to exercise odd totals.

## News adapter

Use the host-supplied `NewsHttpClient`, cursor pagination and declared media/category
capabilities. Return stable article IDs, publication dates, attribution and native
`NewsBlock` content. Excerpts are not full text. Declare `fullText` only when returning
the article body. Verified topic identities belong to the extension; do not attach
an unrelated title merely because two strings look similar. Preserve cancelled
requests and surface partial failures without substituting another article.

## TV adapter

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

The demo restricts URLs to its own HTTPS `/example/` area and rejects path escapes.
That is this adapter's policy, not a hardcoded Nyanime limitation. Adapters needing
additional media hosts should allow only explicit verified origins.

Video/manga share the host client, a bounded timeout, cancellable calls and a
1 MiB response limit. A per-source Mutex coalesces concurrent catalogue fetches
for 60 seconds. Failed responses are not cached. No app-wide client, crawler,
background refresh loop or eager video scan is created. News/TV use supplied HTTP
contracts. Rethrow cancellation; do not hide errors behind endless retries.

Handle no results, removed items, changed markup, missing images, unavailable
streams, malformed dates and offline errors explicitly. Never log tokens/cookies,
put credentials in shared links, or replace missing data with plausible guesses.

## Signing and updates

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
and verifies the resulting signature. `--development` reuses the local demo identity. Native extension API namespace strings are compatibility
identifiers and are retained even when a product uses its own branding.

The optional `assets/nyanime/extension-v1.json` declares distribution identity and
manual/repository update policy. This starter uses manual updates and has no
embedded catalogue. A separately maintained public catalogue is optional; never
bundle its addresses or private signing material into the host.

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

Use [CHECKLIST.md](CHECKLIST.md) for physical-device verification. Compilation and
signature checks do not prove the Home, reader, player or APK trust UI works on
a real phone. Record tested host version and device separately from build results.
