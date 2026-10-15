# One APK, two installation modes

New outputs are release APKs signed with a publisher-owned certificate. The same
file can be installed by Android or imported privately into a supporting Nyanime
version. Imported packages can update without an Android installer dialog.
No catalogue is included or required. Legacy RIN verification is retained for
existing users; `pack.py` does not create new RIN releases.

## Pinned base profiles

| Example | Profile | Compatibility scope |
| --- | --- | --- |
| Video | `aniyomi-video-api`, pinned upstream revision in `sdk/portable-sdk-lock.json` | Hosts implementing anime API 17 and its shared ABI |
| Manga | `aniyomi-manga-api`, pinned upstream revision in `sdk/portable-sdk-lock.json` | Hosts implementing manga API 1.4 and its shared ABI |
| News | `news-api.jar` | Hosts implementing news API 1 |
| TV | `tv-api.jar` | Hosts implementing TV API 1 |
| Guide | `addon-api.jar`, `EpisodeGuideProvider` | Hosts implementing guide API 1 |
| Addon | `addon-api.jar`, `HostedAddon` | Hosts implementing the hosted addon contract |

The old Nyanime export is an optional host SDK, not evidence that an extension
will link on another host. The base video/manga modules compile against the
upstream profiles. Manga uses the common Rx/HTTP entry points and does not
reference Nyanime-only model properties. Home routing remains declarative.

Run checks against actual compiled classes before D8:

```sh
python tools/check_abi.py --profile aniyomi-video-api --classes video/build/tmp/kotlin-classes/release
python tools/check_abi.py --profile aniyomi-manga-api --classes manga/build/tmp/kotlin-classes/release
```

The checker resolves inherited API members and method descriptors. It is not a
replacement for testing the resulting APK on the declared host versions.

## Optional Nyanime code

Keep optional factories in a separate compilation unit/namespace. Only that code
should reference `nyanime.extension.api.SourceCapabilitiesFactory`, custom model
metadata or other host-only types. Declare its name with
`nyanime.optional.factory`; other hosts ignore the metadata. Never reference the
optional implementation from the base source constructor or factory.

Use `--optional-prefix` only for that explicitly separate namespace when checking
the combined compiled output. Do not exclude the base source or common parser.
Retain stable package/source IDs and normal legacy Android feature/class keys.

## Build and sign

```sh
python tools/configure.py
./gradlew :common:test :video:assembleRelease :manga:assembleRelease :news:assembleRelease :tv:assembleRelease :guide:assembleRelease :addon:assembleRelease
python tools/sign_apk.py video --key /private/publisher.pem --certificate /private/publisher.der --build-tools /sdk/build-tools/35.0.1
python tools/sign_apk.py manga --key /private/publisher.pem --certificate /private/publisher.der --build-tools /sdk/build-tools/35.0.1
python tools/sign_apk.py news --key /private/publisher.pem --certificate /private/publisher.der --build-tools /sdk/build-tools/35.0.1
python tools/sign_apk.py tv --key /private/publisher.pem --certificate /private/publisher.der --build-tools /sdk/build-tools/35.0.1
```

`--development` creates/reuses an owned local demo certificate rather than
Android's shared debug certificate. Preserve it for demo updates. Production
publishers must preserve their own signing identity; keys never enter Git or the
downloadable kit. Both installation modes use the same signed bytes.

## Proposed maintainer integration

Existing APK builds can remain unchanged when their base ABI is already
supported. Optional capabilities belong in additional metadata/assets and
separate code. A publisher does not need an exclusive repository, host-specific
source IDs or a second package format. Catalogue listing and execution approval
are independent of distribution as an APK.

Release verification must include Android/private activation, tampering,
interrupted updates, old-version retention, source identity continuity and an
actual supported foreign host. Record host version/API, artifact checksum and
signer in the verification report; do not label untested combinations supported.

The guide example returns no matches rather than fictional classifications. The
addon example creates a hosted view and never schedules background work.
No catalogue or privileged publisher is included in the examples.
