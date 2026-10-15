# Compile-only SDK attribution

Nyanime API sources retain their inherited copyright and Apache-2.0 notices.
The host export is identified by `sdk/sdk-lock.json`.

The independent base ABI profiles are unmodified compile-only API artifacts:

- `aniyomi-video-api.jar`: komikku-app/aniyomi-extensions-lib, revision
  `f5961b5dfb`, Apache-2.0. Source and license:
  https://github.com/komikku-app/aniyomi-extensions-lib/tree/f5961b5dfb
- `aniyomi-manga-api.jar`: keiyoushi/extensions-lib, revision `18a8e26be2`,
  Apache-2.0. Source and license:
  https://github.com/keiyoushi/extensions-lib/tree/18a8e26be2

Exact artifact coordinates and SHA-256 values are recorded in
`sdk/portable-sdk-lock.json`. The root `LICENSE` contains Apache License 2.0.
These artifacts must not be included in extension DEX. Keep the public API
namespaces and inherited notices; a publisher label does not change ownership.

The corresponding Nyanime public source snapshot is available at
https://github.com/owouwuiwi/nyanime/tree/v0.45.0.1. The SDK lock retains the
original build revision and records this public distribution separately.
