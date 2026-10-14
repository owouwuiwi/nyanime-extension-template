# Extension release checklist

## Before building

- [ ] Choose unique package/source IDs and keep them stable for future versions.
- [ ] Pin a matching compile-only SDK; retain license and attribution notices.
- [ ] Review every URL, selector, timestamp, model field and supported capability.
- [ ] Remove demo IDs and labels when publishing your own adapter.
- [ ] Confirm you have rights to publish the content and metadata you distribute.

## Automated checks

- [ ] `python -m unittest discover -s tests -v` passes.
- [ ] `./gradlew :common:test` and the selected module's build pass.
- [ ] RIN verification passes; no host/shared classes enter DEX.
- [ ] Empty results, filtered pagination, malformed data and failed requests are covered.
- [ ] Source URLs and references remain stable; fetch time is not publication time.
- [ ] Source code/archive contains no private keys, credentials or machine paths.

## On a physical device

- [ ] Explicitly review/approve the signer; test initial import and a higher version.
- [ ] Enable the source language, select its Home categories and reorder them.
- [ ] Confirm one extension contributes multiple independently scoped categories.
- [ ] Test all sections, genre/date filters, search and next-page exhaustion.
- [ ] Open a detail page; play each quality/subtitle or read every page in order.
- [ ] Test an odd-page chapter, rotation and return without losing progress.
- [ ] Check News articles or TV unavailable-guide state when using those examples.
- [ ] Test offline, cancellation, slow responses and retry; no infinite loading.
- [ ] Test source disable/removal, saved library entries and missing-source messages.
- [ ] Verify narrow layouts, large text, light/dark themes and reduced motion.
- [ ] Check room/Cast/PiP paths separately if supported; do not infer from local playback.

## Publish

- [ ] Increase `versionCode`, retain package/source IDs and publisher key.
- [ ] Package with an owned signer; review the public fingerprint and SHA-256 report.
- [ ] Keep signing keys out of Git and downloadable archives.
- [ ] Distribute source, required licenses, build instructions and an honest test record.
