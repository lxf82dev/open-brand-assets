# Source adapters

The helper searches these collections; it does not mirror them. All source requests are public and unauthenticated. A source failure is reported separately from a successful search with zero matches.

| Source | Lookup | Coverage and constraints |
| --- | --- | --- |
| [Open Brand Assets](https://github.com/lxf82dev/open-brand-assets) | Local `catalog.json`, otherwise `https://raw.githubusercontent.com/lxf82dev/open-brand-assets/main/catalog.json` | Complementary brands and official variants with hashes, retrieval dates, usage notes, and original URLs. MIT applies to our code; brand assets keep their own rights. |
| [SVGL](https://github.com/pheralb/svgl) | `https://api.svgl.app/` | Full-color logos, wordmarks, theme variants, and `brandUrl` where supplied. MIT repository license; inspect brand terms separately. |
| [Lobe Icons](https://github.com/lobehub/lobe-icons) | GitHub `master` tree, `packages/static-svg/icons/*.svg` | AI providers and models. Results link to exact SVGs at the returned commit SHA. MIT repository license. |
| [Simple Icons](https://github.com/simple-icons/simple-icons) | GitHub `develop` tree, `icons/*.svg` | Monochrome brand icons. CC0 collection; individual brand rights and restrictions still apply. Read the matching entry in `data/simple-icons.json` for guidelines/source/license metadata. |
| [theSVG](https://github.com/glincker/thesvg) | GitHub `main` tree, `public/icons/<brand>/*.svg` | Broad brand and cloud-service coverage. Results link to exact variants at a commit SHA. MIT repository license. |

`search --source <name>` narrows the search; names are `ours`, `svgl`, `lobe`, `simple-icons`, and `thesvg`. Use `--limit` for results **per source**, and `--refresh` after a reported catalog update. JSON includes each source's lookup time, cache flag, commit where available, total matches, and failures. Cached catalogs expire after 24 hours; failures do not fall back silently to expired data. `--offline` uses only a full local checkout, regardless of `--source`.

GitHub's unauthenticated rate limit may affect upstream tree requests. Use the upstream website or an existing authenticated GitHub tool if that occurs. Do not send credentials to asset hosts. If an adapter format changes, inspect the linked upstream data and update the adapter; do not interpret a parser error as an absent brand.

The helper searches normalized names and filenames. It does not use fuzzy matching, translate names, or resolve model-to-company relationships. Try spelling/parent-company aliases deliberately. Upstream library licenses and notices remain upstream's, and may change; check the selected revision when redistributing their files.
