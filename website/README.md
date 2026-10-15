# Nyanime extension starter

Six independent extension examples and **one complete developer guide**.
Learn the public APIs, adapt a website, declare Home categories, build, sign,
install and maintain an extension without changing Nyanime.

**[I already build AniYomi/Mihon extensions](docs/GUIDE.md#for-existing-extension-authors)** ·
**[This is my first extension](docs/GUIDE.md#set-up-and-build-the-unchanged-example)** ·
[Read on the website](https://owouwuiwi.github.io/example/guide/) ·
[Explore the original demos](https://owouwuiwi.github.io/example/)

| Example | Demonstrates | Installable output |
| --- | --- | --- |
| Video | Two Home categories, search, genres, dates, episodes, qualities, subtitles | `.apk` |
| Manga | Home, filters, chapters, original page order, odd-length chapters | `.apk` |
| News | Feed, search, pagination, native article blocks | `.apk` |
| TV | Channels, lookup, playback, explicit missing-guide state | `.apk` |
| Guide | Component-free work search, explicit no-results state | `.apk` |
| Addon | Component-free hosted UI, appearance and return navigation | `.apk` |

One publisher-signed APK can be **installed through Android** or **imported privately
into a supporting Nyanime version**. No catalogue is included or required. Existing
compatible sources do not need a rewrite. A manually imported file has manual
updates until the user explicitly associates a compatible origin.

The guide explains each family's methods and models with code examples,
a release checklist and troubleshooting. Matching compile-only SDK JARs and
API reference sources, Gradle wrapper, signing tools, fixtures and tests are included.

Download the [complete kit](https://owouwuiwi.github.io/example/downloads/v1.0.2/placeholder-extension-kit.zip),
or use this repository as a GitHub template. The refreshed kit/guide is v1.0.2;
the signed reference APKs remain the unchanged, verified v1.0.1 artifacts. Optional prebuilt examples require
explicit publisher approval:

[Video APK](https://github.com/owouwuiwi/nyanime-extension-template/releases/download/v1.0.1/placeholder-video-1.0.1.apk) ·
[Manga APK](https://github.com/owouwuiwi/nyanime-extension-template/releases/download/v1.0.1/placeholder-manga-1.0.1.apk) ·
[News APK](https://github.com/owouwuiwi/nyanime-extension-template/releases/download/v1.0.1/placeholder-news-1.0.1.apk) ·
[TV APK](https://github.com/owouwuiwi/nyanime-extension-template/releases/download/v1.0.1/placeholder-tv-1.0.1.apk) ·
[Guide APK](https://github.com/owouwuiwi/nyanime-extension-template/releases/download/v1.0.1/placeholder-guide-1.0.1.apk) ·
[Addon APK](https://github.com/owouwuiwi/nyanime-extension-template/releases/download/v1.0.1/placeholder-addon-1.0.1.apk) ·
[Verification and fingerprints](VERIFICATION.md)

**Nyanime does not promote piracy in any way or form.** We follow a
**bring-your-own-content** model. This starter uses original geometric drawings,
sample text and intentionally black, silent videos. The finite TV test file is
not a real broadcast. Use only material you are legally entitled to access.
[Responsible use](https://owouwuiwi.github.io/responsible-use/).

Code: Apache-2.0, with inherited API notices retained. Original demo media:
CC0-1.0; branding and fonts retain their own notices. See
[media credits](website/ASSETS.md). An APK extension is signed executable code, not a sandbox.
No catalogue is included or required.
