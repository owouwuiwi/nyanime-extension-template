# APK interoperability verification

Verified on 15 October 2026. Host source revision:
`8ef5b7fe9ce8cd84adbf5b5a214e7b144d3972b2`.

## Automated evidence

- Nyanime: 1,497 app JVM tests passed; targeted extension/import/Store checks
  repeated after the first-consent correction.
- Starter: 24 Python tooling/fixture/ABI policy tests passed.
- All six release modules compiled; signatures verified by Android apksigner.
- Video and manga base bytecode checked against their independently pinned upstream
  APIs. All six checked against the exported Nyanime compile-only SDK.
- Developer kit hashes checked; no private keys or build directories included.

## Physical-device scope

Galaxy Z Flip6, Android 16, production-signed Nyanime 0.45.0.1 (build 238).
AniYomi 0.18.2.1 and Mihon 0.21.2 were used only for the declared portable profiles.
Tests use original synthetic media, not a real content provider.

| Host | APK | Runtime path |
| --- | --- | --- |
| AniYomi 0.18.2.1 | Video, base API 17 | Android install, individual approval, catalogue, details, episodes and native playback |
| Mihon 0.21.2 | Manga, base API 1.4 | Android install, individual approval, catalogue, details, chapters and actual reader page |
| Nyanime 0.45.0.1 | Video | Private import without a catalogue, signature approval, Android copy removed outside playback, then native playback from the retained private copy (0:02 / 0:12) |
| Nyanime 0.45.0.1 | Manga | Private import without a catalogue, Android copy removed outside reading, then actual page 1 / 6 from the retained private copy |
| Nyanime | News | Private import, native article Home and filters |
| Nyanime | Guide | Private import and provider settings; no invented classifications |
| Nyanime | Hosted addon | Private import, hosted original view and return to the host |
| Nyanime 0.45.0.1 | TV | Original APK validation and provider settings; first-consent activation and finite native playback additionally tested with a fresh-package-identity variant of the same synthetic example |

News, guide and addon runtime checks were performed on the preceding build in
this verification sequence; their loading paths remained covered by the final
targeted suite. The final production APK additionally rejected altered APK bytes
and a different publisher certificate without replacing the active private copy.
Activation was refused while a playback session was still active, as intended.

The foreign-host APK bytes are the same signed artifacts listed below, not
separate host builds. Compatibility is conditional on the actual family and ABI
implemented by the host; this report does not cover other host versions.

## Signed example identity

Publisher certificate SHA-256:
`ab5f53f144be77afa1fb5dea6829e79f9170f2b28fda2ee073f1c960eef25b4e`.
This local demo identity is not a shared Android debug key. Approve it only when
intentionally testing these examples; it is not a privileged publisher in Nyanime.
Private signing material is excluded from Git, the SDK and the kit.

| APK family | SHA-256 |
| --- | --- |
| video | `fd7fb2bef3228117c9274cb7c958a3b09e2a74252665e6a007427c1295d07506` |
| manga | `6afdbaeb1808a762ff4c865f907901317e4199d8ede0db9fbb41b588aaf43f58` |
| news | `aa42bdad566f873c50062c3c47e104d39bdad86074c3d6829a670f7c37a21a82` |
| tv | `65dad1ef085d9e94370619bd746ce0704bfdebc01d3e1cd478e93b31c356f399` |
| guide | `b11f3ef6be214e926ef20306f88e9a3a71f0e6fa0f8f15df3ea1c4c5e1419c20` |
| addon | `ab71c3695ee5efc79a1fd5fa4cb22f72e70778ad8449ea0fce192d780ddba6ce` |

## Limits

The TV example is a finite black silent test signal, not a live broadcaster.
The guide deliberately returns no fabricated classifications. The addon only
creates a hosted view and returns to Nyanime. Unit/build results do not prove
real-device synchronization, live timing or every possible provider implementation.
Periodic updates depend on Android WorkManager and network availability; the
six-hour interval is not a guarantee that Android runs a job at an exact second.
