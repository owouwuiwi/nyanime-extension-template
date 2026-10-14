# Build your first Nyanime extension

A working starter, with an original demo website and four independent examples.
**Start here.** Use the [technical reference](docs/REFERENCE.md) when adapting it.

| Example | Demonstrates | Installable output |
| --- | --- | --- |
| Video | Two Home categories, search, genres, dates, episodes, qualities, subtitles | `.rin` |
| Manga | Home, filters, chapters, original page order, odd-length chapters | `.rin` |
| News | Feed, search, pagination, native article blocks | `.apk` |
| TV | Channels, lookup, playback, explicit missing-guide state | `.rin` |

Everything is extracted from [our demo website](https://owouwuiwi.github.io/example/).
Videos are intentionally black, with a silent audio track. Manga pages are original
geometric drawings. The TV signal is a **finite test file**, not a real broadcast.

**Nyanime does not promote piracy in any way or form.** We follow a
**bring-your-own-content** model. This separate starter uses only original demo
material; use content you are legally entitled to access and respect copyright.
[Responsible use](https://owouwuiwi.github.io/responsible-use/).

## 1. Get ready

Install **JDK 17**, **Android SDK 36 / Build Tools 35.0.1**, and **Python 3.10+**.
Set `JAVA_HOME` and `ANDROID_HOME`, or put `sdk.dir=/your/android/sdk` in
`local.properties`. On Windows, use `gradlew.bat` instead of `./gradlew`.

The matching compile-only SDK, reference API sources and Gradle wrapper are
included. To refresh the SDK from a matching Nyanime checkout:

```sh
python tools/prepare_sdk.py --host /path/to/nyanime --build
```

Install the small packaging/test dependency once:

```sh
python -m pip install -r requirements-tools.txt
```

## 2. Configure

The unchanged demo works as-is. For your own extension, edit `template.json`:
choose a unique package, a stable positive source ID, name, language and website.
Then generate matching Android metadata and Home declarations:

```sh
python tools/configure.py
```

Keep package, source IDs and signing key unchanged when updating an extension.
Increase `versionCode` for every published change. Do not ship the demo's IDs as
your own product. The source implementation lives in each module's `*Source.kt`;
the website parser lives in `common/`. Nyanime needs no site-specific changes.

## 3. Build and test

```sh
python -m unittest discover -s tests -v
./gradlew :common:test :video:assembleDebug :manga:assembleDebug :news:assembleDebug :tv:assembleDebug
```

Choose one module when you only need one example. Android APKs are build
containers for the RIN examples; the news example currently uses APK installation.

## 4. Make your RIN

```sh
python tools/pack.py video --development
python tools/pack.py manga --development
python tools/pack.py tv --development
```

Files appear in `dist/`. Your development identity is created once in `.local/`;
**back it up privately and never commit it**. For publishing, use your own key
and DER certificate with `--key` and `--certificate`. See [signing](docs/REFERENCE.md#signing-and-updates).

## 5. Open in Nyanime

Use a host supporting standalone local RIN import (version code **232+**).
Open **Store → Load RIN**, choose the file, review its publisher,
and explicitly approve it. Enable **English** sources if they are hidden.

The video extension declares **DEMO Animation** and **DEMO Cartoons**. Both can
appear among the selectable Home categories; the manga extension adds **DEMO Manga**.
Enable/reorder them in Home settings as needed. They disappear when the last
enabled contributing extension is removed. A catalogue is not required for local import.

For local news development, install `news/build/outputs/apk/debug/news-debug.apk`,
approve the source and select it in News. For distribution, build `:news:assembleRelease`
and use `tools/sign_apk.py` with an owned publisher key; see the technical reference. Never install both an APK and a RIN copy of the same source.

Prebuilt demos: [Video RIN](https://owouwuiwi.github.io/example/downloads/placeholder-video-1.0.0.rin) ·
[Manga RIN](https://owouwuiwi.github.io/example/downloads/placeholder-manga-1.0.0.rin) ·
[News APK](https://owouwuiwi.github.io/example/downloads/placeholder-news-1.0.0.apk) ·
[TV RIN](https://owouwuiwi.github.io/example/downloads/placeholder-tv-1.0.0.rin).
[Publisher fingerprint and checksums](https://owouwuiwi.github.io/example/downloads/demos.json).
These optional demos are separate from the application and use an owned demo signing identity.

## Make it yours

An extension can declare **multiple Home categories**. For example, a cartoons
provider declares `homes[].id = "cartoons"`, its label, sections and supported
filters. Nyanime reads that contract: it never guesses a category from a source's
name. **Home categories are navigation destinations; genres are filters inside them.**

Read [the complete reference](docs/REFERENCE.md), then use the
[release checklist](docs/CHECKLIST.md). Regenerating with `configure.py` overwrites
the generated manifests and Home JSON: change the generator when keeping custom declarations.

Code: Apache-2.0, with inherited API notices retained. Generated demo media:
CC0-1.0; see [ASSETS.md](website/ASSETS.md). No third-party series, scans or streams
are included. The app stays generic; this optional extension owns every demo URL,
selector and parsing rule.
