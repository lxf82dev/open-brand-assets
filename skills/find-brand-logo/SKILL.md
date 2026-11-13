---
name: find-brand-logo
description: Find and retrieve existing company, product, and AI provider logos with provenance from Open Brand Assets, SVGL, Lobe Icons, Simple Icons, and theSVG. Use when a task needs real brand assets or a missing logo contributed; excludes designing or redrawing a logo.
---

# Find Brand Logo

Use existing artwork and retain its source. This skill includes a standalone Python 3.10+ CLI; resolve `scripts/logos.py` relative to this skill directory. It works both inside the repository and when only this skill folder is installed. No API keys or Python packages are required.

## Find a suitable asset

Run `python3 <skill-directory>/scripts/logos.py search "brand name" --json`.

The default searches our complementary catalog plus SVGL, Lobe Icons, Simple Icons, and theSVG. Results include source URLs, variants, and available guideline metadata. `--refresh` bypasses the 24-hour cache. Check `errors` before concluding a brand is missing; an unavailable source has not been checked. Try the product name, parent company, and known aliases when needed.

Prefer official brand-kit artwork for the requested product and visual context. Our catalog supplies dated provenance and background hints; upstream collections can have better coverage. A website favicon is labelled `site-icon`, and is not evidence that a full logo or vector version exists. Inspect the actual artwork before using it. Choose supplied light/dark/color/wordmark variants; do not redraw or recolor a trademark to approximate a missing variant.

Confirm the actual company/product behind a match: names can collide. For example, Simple Icons' `flux` is the CNCF Flux project, not Black Forest Labs' FLUX image models. Check its source metadata before choosing it.

If freshness matters, verify the current official brand page and compare it with the result's recorded date. A recent download does not establish that a vendor has not changed its identity. Results from GitHub upstreams use a commit-pinned asset URL.

## Retrieve and report

For our catalog, fetch an exact variant with:

```bash
python3 <skill-directory>/scripts/logos.py fetch openrouter --variant glyph-ink --output <project>/public/logos/openrouter.svg
```

The CLI verifies the recorded SHA-256 and image format, rejects unsupported active SVG content, and refuses to overwrite files without `--force`. In a full checkout, `--offline` searches and retrieves local files without network access. A separately installed skill retrieves our current catalog and assets from `lxf82dev/open-brand-assets` on GitHub.

For an upstream result, retrieve its returned URL with the available download tool, preserve required upstream attribution/license notices, inspect the bytes, and record the source URL, variant, retrieval date, and file hash alongside the output. Read [source details](references/sources.md) when selecting a library or handling a failed adapter.

Report the chosen source and any relevant usage condition with the delivered file. `guidelines-available` means guidelines exist, not blanket approval. `permission-required` and `unverified` are unresolved conditions; do not silently describe those assets as cleared. Repository licenses do not grant rights to vendor trademarks. Check the actual terms for the intended context, and distinguish editorial reference from marketing or endorsement.

## Fill a gap

When the collections miss a brand or current official variant, inspect the vendor's official brand/media page first, then its own website icons. Record the exact source, date, and modifications; label a site icon honestly. If no suitable asset exists, report the gap instead of generating a replacement.

If the user requested a contribution, follow `CONTRIBUTING.md` in a checkout of [Open Brand Assets](https://github.com/lxf82dev/open-brand-assets). Use one brand folder, preserve upstream notices when applicable, rebuild the catalog, and run the checks. Finding a logo alone does not authorize a GitHub write or changes to an unrelated repository.
