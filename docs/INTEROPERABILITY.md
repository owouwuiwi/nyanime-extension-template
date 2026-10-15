# APK interoperability

The canonical workflow now lives in [the complete developer guide](GUIDE.md).
It has two entry points, not two competing sets of instructions:

- [Existing AniYomi/Mihon extension authors](GUIDE.md#for-existing-extension-authors).
- [Your first extension](GUIDE.md#set-up-and-build-the-unchanged-example).

## Pinned base profiles

The [profile lock](../sdk/portable-sdk-lock.json) records exact upstream artifacts
and SHA-256 hashes. [SDK-NOTICE.md](../SDK-NOTICE.md) retains attribution.
Use the guide's ABI matrix and check compiled descriptors; API numbers alone are
not compatibility evidence. [VERIFICATION.md](../VERIFICATION.md) states the real
device/host scope and artifact identities.

## Optional Nyanime code

See [Isolate optional capabilities](GUIDE.md#isolate-optional-capabilities).
The base factory must load without Nyanime-only classes. Optional attachment must
preserve the ordered medium/source identities.

## Build and sign

Use [Signing and updates](GUIDE.md#signing-and-updates). New outputs are one signed
APK for Install or Import; keep the same publisher identity across updates.
Legacy RIN reading/restoration remains supported. Tools do not create new RINs,
and renaming an archive does not convert it.

## Proposed maintainer integration

A working upstream-compatible source does not need a rewrite or a second package
format. Test the existing APK first, add declarative or isolated optional features
only as needed, and verify the final artifact on each host/version claimed.
See [Install and check the result](GUIDE.md#install-and-check-the-result) for
consent, origin association, updates and deferred atomic activation.
