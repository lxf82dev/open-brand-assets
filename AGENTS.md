# Open Brand Assets

Python 3.10+ standard library only. Work from the repository root.

- `python3 scripts/catalog.py` validates manifests and regenerates `catalog.json`.
- `python3 scripts/catalog.py --check` verifies the committed catalog.
- `python3 -m unittest discover -s tests -v` checks search, source adapters, downloads, and validation without network access.
- The installable skill and its standalone CLI live under `skills/find-brand-logo/`. Keep it usable when that folder alone is installed; do not make it import root-level code or depend on a fixed checkout path.
- Preserve source bytes. Add exact source URLs, dated provenance, SHA-256, honest role/theme labels, and rights notes in `brands/<id>/brand.json`.
- Brand images are excluded from the root MIT grant. Do not treat a public download, an upstream repository license, or `guidelines-available` as blanket trademark permission.
- Catalogs are generated from manifests. Network lookup failures must remain visible and distinct from zero matches. Do not run network checks in contributor PR CI.
