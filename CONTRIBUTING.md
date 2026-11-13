# Contributing

Add a missing brand, a current official variant, or a correction to source/usage information. Look in our catalog and the four upstream collections first; a dated official variant or a useful source record can still be worth adding when a brand exists elsewhere.

## Add or update a brand

1. Find the official brand/media kit. If none is available, an icon served by the vendor's own website is acceptable when labelled `site-icon`. Do not recreate a logo or use an image-search thumbnail as its source.
2. Create `brands/<lowercase-brand-id>/`, or reuse the existing folder. Add unmodified SVG or PNG files with descriptive names. Prefer supplied light/dark variants over recoloring. Record any essential conversion or sanitization in `source.modifications`; never claim modified bytes are the untouched original.
3. Copy a similar `brand.json` and update its fields. An asset `id` is unique within that brand; `file` is the repository-relative path. Use `role` values `symbol`, `wordmark`, `lockup`, `site-icon`, or `app-icon`, and `theme` values `light`, `dark`, or `any`.
4. Record the source page, exact download URL, retrieval date (`YYYY-MM-DD`), source kind, and SHA-256. For archives, retain the archive URL and exact `archive_member`; do not replace it with an invented direct URL. Mention embedded raster artwork in an SVG's `note` field.
5. Record rights honestly. Use `guidelines-available` when you have an official guideline URL, `permission-required` when published conditions require approval, `unverified` when the terms have not been established, or `owner-supplied` for assets supplied by the owner. Add a dated note; never infer a blanket trademark permission from an open-source repository license. No confidential permissions or private correspondence in the public repository.
6. Run the commands below and include `catalog.json` with the change. In the PR description, explain the source, what changed, and why the addition is useful. Include any applicable upstream license/attribution notices when importing upstream artwork.

```bash
python3 -c 'import hashlib,pathlib; print(hashlib.sha256(pathlib.Path("brands/example/symbol.svg").read_bytes()).hexdigest())'
python3 scripts/catalog.py
python3 scripts/catalog.py --check
python3 -m unittest discover -s tests -v
```

The CLI and checks require Python 3.10+ and no external dependencies. `catalog.py` is the source of validation rules. Manifests require nonempty `name`, HTTPS `website`, `aliases` (an array), and `categories` (a nonempty array); asset source kinds are `official-brand-kit`, `official-website`, `owner-supplied`, and `upstream-library`. Each asset requires a rights license identifier and explanatory note. See an existing [manifest](brands/openrouter/brand.json) for the complete shape.

Preserve owner bytes where possible. SVG scripts, foreign objects, external resource references, entity declarations, and active CSS are unsupported. Embedded PNG data is permitted so official files that contain raster elements can remain unchanged. Keep files under 5 MiB. If a source cannot be distributed under the available conditions, propose a source-link entry or request rather than uploading it.

## Search adapters and the skill

The standalone helper is `skills/find-brand-logo/scripts/logos.py`; the root `logos.py` is only an entrypoint. Test both full-checkout behavior and skill-folder-only behavior when changing catalog resolution. Keep network requests bounded, preserve source failures in JSON, and add fixtures for upstream response changes. CI runs offline; live smoke checks should use public data and never include credentials in output or committed fixtures.

The [coverage snapshot](research/upstream-coverage.json) describes a one-time filename/alias check. Update it only after checking actual upstream trees and recording their revisions. It is not used as a runtime allowlist and does not establish trademark clearance.

## Corrections and removal

Use the appropriate issue template with the brand, affected path, official evidence, and requested change. For rights-holder requests, see [TRADEMARKS.md](TRADEMARKS.md).
