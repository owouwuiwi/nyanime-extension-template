# Verification record

Host SDK: Nyanime 0.43.0.3, API modules freshly built before export.

- All four Android example modules compile successfully.
- 10 JVM tests pass: parser, scoped Home data, pagination, ordering, original page order, URL boundaries, shared cache, failures and cancellation.
- 16 Python tests pass: configuration, signing, altered payloads, DEX guard, website links and original-media checksums.
- Three source RINs are signed and verified without executing code.
- DEX inspection finds only starter implementation classes and the exact D8-generated LambdaMethod annotation; no bundled host or shared runtime classes.

Physical-device Home/import/playback verification has not yet been completed for these demo artifacts. Build and integrity results are not a substitute for that checklist. News uses APK distribution; the current host does not support news RIN.

The website was checked in the browser at desktop, 390 px and 320 px widths, with light/dark themes, reduced motion, live demo filters and video quality changes. These web checks are separate from the remaining Android-device checklist.
