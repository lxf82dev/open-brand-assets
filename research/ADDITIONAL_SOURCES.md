# Additional logo-source research

Checked **2026-11-13**. We already search SVGL, Lobe Icons, Simple Icons, and theSVG alongside our own files. This pass adds six more adapters rather than copying their assets into our catalog.

| Source / CLI name | Why add it | Asset lookup and verification |
| --- | --- | --- |
| [Gilbarbara Logos](https://github.com/gilbarbara/logos) / `gilbarbara` | Optimized developer/DevOps artwork, including a Higgsfield wordmark that complements our website icons. | Actual `logos/` paths plus names, file lists, and shortnames from `logos.json`. Live Higgsfield search and SVG verified. |
| [Vector Logo Zone](https://github.com/VectorLogoZone/vectorlogozone) / `vectorlogozone` | Standardized icon/tile/horizontal layouts across many brands. | Actual `src/content/logos/<brand>/` paths. Live GitHub search and SVG verified. Its current layout differs from older `/www/logos/` examples; the adapter indexes the current source directory. |
| [Devicon](https://github.com/devicons/devicon) / `devicon` | Programming-language, design, and developer-tool identities. | Actual `icons/<tool>/` paths with `altnames` from `devicon.json`. Live `arm64` lookup resolved to the supplied aarch64 artwork. |
| [selfh.st Icons](https://github.com/selfhst/icons) / `selfhst` | Self-hosted and other application/service logos. | Names/references from `index.json`; actual SVG paths, with PNG-only fallback. Live Nextcloud search and SVG verified. |
| [Dashboard Icons](https://github.com/homarr-labs/dashboard-icons) / `dashboard-icons` | A second curated service/dashboard collection, with useful format coverage and variants. | Actual repository `svg/` paths and PNG-only fallback. Live Nextcloud search and SVG verified. Its external federated sources are not recursively re-indexed. |
| [Cryptocurrency Icons](https://github.com/spothq/cryptocurrency-icons) / `crypto` | Currency identities and styles; filenames alone are often just ticker symbols. | Actual `svg/{black,color,icon,white}/` paths plus names/symbols from `manifest.json`. Live Bitcoin and BTC matching and SVG verified. Original/editing directories are excluded. |

All examples use commit-pinned download URLs. The [machine-readable verification record](additional-sources.json) records exact revisions, indexed asset counts, example URLs, and project license links. Asset counts include variants and overlap between sources; they are not unique-brand counts or a freshness guarantee for every individual mark.

## Rights and contributor credit

- Gilbarbara Logos: CC0-1.0 project; its README reserves original brand ownership.
- Vector Logo Zone: AGPL-3.0 covers website code. Its README separately retains brand-owner rights and places its modifications in the public domain. The adapter returns this distinction explicitly.
- Devicon: MIT project; original brand rights remain separate.
- selfh.st Icons: CC-BY-4.0 collection. Attribution is returned in both plain-text and JSON lookup output. Keep that credit, license link, and applicable brand conditions when using an asset.
- Dashboard Icons: Apache-2.0 project; retain applicable notices and check brand-specific restrictions.
- Cryptocurrency Icons: CC0-1.0 project; check the actual currency identity and any applicable brand rights.

License files were fetched from the same revisions as the verified examples. The [README credits](../README.md#credits-to-the-people-building-the-commons) link the maintainers and contributor lists for every integrated project. We do not import their implementations or bulk-vendor their collections.

## Reviewed but deferred

[benc-uk/icon-collection](https://github.com/benc-uk/icon-collection) is useful for cloud-architecture diagrams. Its README describes heterogeneous sources and use-specific Microsoft conditions, and the repository has no single detected root license. It also includes archive and non-brand resource artwork. We deferred a generic adapter rather than assign one blanket license or mix architecture-resource symbols into ordinary brand searches. It remains a useful manual source for a task that specifically needs those diagrams.

Gilbarbara Logos, selfh.st, and Cryptocurrency Icons have upstream-specific request/contribution policies. Follow those policies rather than assuming our own open contribution process applies to them.
