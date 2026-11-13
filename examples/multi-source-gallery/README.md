# Multi-source HTML integration example

This example uses the actual `find-brand-logo` CLI to select and retrieve twelve images across all eleven supported collections. It covers SVG, PNG, and an official SVG that contains embedded PNG artwork.

## Build and open

Python 3.10+, no packages or API keys. Run from the repository root:

```bash
python3 examples/multi-source-gallery/build.py
```

Open `examples/multi-source-gallery/generated/index.html` in a browser. No server is needed.

- **Live sources** loads the exact asset URLs returned by the skill. The page reports each image's decode status.
- **Saved copies** uses the image bytes embedded in the HTML. The images are self-contained after the build; this mode needs no image requests.
- **Provenance & rights** exposes each selected variant, checksum, source URL, and available usage or attribution notes.

The build writes source images, original collection notices, a provenance `manifest.json`, and the portable HTML into `generated/`. Those outputs are ignored by Git; this repository does not vendor the upstream image collections through the example. Use `--output <directory>` or `--cache-dir <directory>` to choose other locations. Rebuilding replaces this example's named output files.

The builder captures the CLI's structured output in Python rather than placing full catalogs or image bytes in the agent's context. It selects explicit variants: in particular, Vercel's supplied black artwork for a white tile. It preserves image bytes and required attribution; it does not recolor marks.

## Browser verification

The [recorded run](../../research/multi-source-browser-test.json), checked on 2026-11-13, verified:

- All twelve live image requests returned HTTP 200 and decoded to nonzero dimensions.
- All twelve saved-copy images decoded, with every `currentSrc` using a data URL.
- The live/saved toggle and provenance disclosure worked.
- Desktop (1400px) and mobile (390px) layouts had no horizontal overflow or JavaScript errors; light/dark appearances were inspected.

This run found a real integration issue: our PNG search results omitted their `format`. The helper now returns it, and a regression test checks selecting and retrieving the PNG using that metadata.

This is an opt-in network example, not a network-dependent CI test. It samples twelve assets, not every mark or variant in each collection. The browser's network was not globally disabled for the saved-copy check; data URLs establish that the images themselves need no external fetch. Check official brand terms for your intended use; a successful image load is not usage clearance.
