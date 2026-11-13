# Open Brand Assets

Real logo files with sources, dates, variants, and an agent skill that searches across five public collections.

We started this after repeatedly hunting down AI-provider logos for Stitchable. Existing collections solve most of the problem. This repository fills gaps and keeps current official variants with enough provenance to revisit them later. It is a small complementary library, not a mirror of those projects.

## The initial collection

39 files across eight brands, collected on **2026-11-13**:

| Brand | What is included | Source |
| --- | --- | --- |
| [HeyGen](brands/heygen/) | 15 official SVGs: symbol, full, secondary, and tertiary lockups | [Official brand kit](https://www.heygen.com/brand-kit) |
| [Higgsfield](brands/higgsfield/) | Website and touch icons, PNG | [Official website](https://higgsfield.ai/) |
| [Runware](brands/runware/) | Website icon and white wordmark, SVG | [Official website](https://runware.ai/) |
| [LibTV](brands/libtv/) | Website touch icon, PNG | [Official website](https://www.liblib.tv/) |
| [Black Forest Labs](brands/black-forest-labs/) | Black/white symbol and logotype, SVG | [Official brand page](https://bfl.ai/brand) |
| [OpenRouter](brands/openrouter/) | Glyph, horizontal, and vertical in grape/volt/ink/cloud, SVG | [Official brand page](https://openrouter.ai/brand) |
| [Stitchable](brands/stitchable/) | Owner-supplied color and mono glyphs, SVG | [Stitchable](https://stitchable.ai/) |
| [EditableFrames](brands/editableframes/) | Owner-supplied app icon, SVG | [EditableFrames](https://editableframes.stitchable.ai/) |

The [coverage snapshot](research/upstream-coverage.json) records the four upstream commit SHAs and matching SVG paths. Six of these brands had no matching brand paths in those snapshots: HeyGen, Higgsfield, Runware, LibTV, Stitchable, and EditableFrames. This is a filename/alias check, not proof that every upstream historical release lacks them. BFL and OpenRouter already have upstream coverage; our entries provide official downloads and dated source records.

Files are preserved byte-for-byte. HeyGen's three symbol SVGs contain embedded PNG artwork in the official kit; they are labelled in metadata and are not fully vector images. Site icons are labelled `site-icon` rather than presented as full brand kits. Recorded dates mean when we collected or checked a source, not a promise that the brand has never changed since.

## Find a logo

Python 3.10+; no packages or API keys required.

```bash
git clone https://github.com/lxf82dev/open-brand-assets.git
cd open-brand-assets
python3 logos.py search "HeyGen" --json
python3 logos.py search "Claude" --source lobe
python3 logos.py search "OpenRouter" --refresh
```

The default searches our catalog plus [SVGL](https://github.com/pheralb/svgl), [Lobe Icons](https://github.com/lobehub/lobe-icons), [Simple Icons](https://github.com/simple-icons/simple-icons), and [theSVG](https://github.com/glincker/thesvg). It returns actual asset URLs. GitHub upstream results are pinned to the retrieved commit. `--limit 10` limits results **per source**, so one large collection cannot hide another's matches.

Public catalogs are cached locally for 24 hours. Use `--refresh` to bypass that cache. JSON reports the lookup time, cached status, and failures for each source. An unavailable source is not treated as a successful lookup with no matches. GitHub public API rate limits can apply.

To retrieve a file from this repository:

```bash
python3 logos.py fetch openrouter --variant glyph-ink --output ./public/logos/openrouter.svg
python3 logos.py search "LibTV" --offline --json
```

`fetch` verifies the SHA-256 and image format, prints provenance and usage notes, and refuses to replace an existing file unless `--force` is supplied. It retrieves our variants; download upstream candidates from the URLs returned by `search`, with their required notices. `--offline` requires a full checkout and uses only its local catalog/files.

The machine-readable [catalog.json](catalog.json) is generated from `brands/*/brand.json`. Assets can also be consumed directly from GitHub; pin a commit for reproducible builds:

```text
https://raw.githubusercontent.com/lxf82dev/open-brand-assets/<commit>/brands/openrouter/glyph-ink.svg
```

## Install the agent skill

The Skills CLI requires Node.js 22.20+. You can also use the manual copy option below without Node.

```bash
npx skills add lxf82dev/open-brand-assets --skill find-brand-logo
```

Or copy `skills/find-brand-logo/` into your agent's supported skills directory. The folder is self-contained: when installed alone, its Python helper reads our public GitHub catalog and assets; in a full checkout, it reads the local catalog. There is no fixed path or dependency on this repository being cloned elsewhere.

Ask the agent: **“Use find-brand-logo to get the current HeyGen symbol for a light background and record its source.”** The skill searches all five collections, checks official variants and source dates, and surfaces usage conditions. It does not invent or redraw missing logos.

## Contribute

Missing brand? New official identity? Better source or guideline information? See [CONTRIBUTING.md](CONTRIBUTING.md), or open a logo request with an official source URL.

```bash
python3 scripts/catalog.py
python3 scripts/catalog.py --check
python3 -m unittest discover -s tests -v
```

Contributions validate file hashes, source metadata, supported image content, manifest consistency, and catalog freshness in CI. Network access is not required for those checks.

## License and credits

Our original code, documentation, and skill are [MIT licensed](LICENSE). **Brand images retain their owners' rights and are excluded from that grant.** A public download does not establish permission for every use or redistribution. Each manifest records what has and has not been verified; consult [TRADEMARKS.md](TRADEMARKS.md) and the official guidelines for your context.

The collection borrows the ideas of SVG-first assets, variants, community submissions, and brand-guideline links from [SVGL](https://github.com/pheralb/svgl), [Lobe Icons](https://github.com/lobehub/lobe-icons), [Simple Icons](https://github.com/simple-icons/simple-icons), and [theSVG](https://github.com/glincker/thesvg). The adapters link to those projects without vendoring their collections. Their code and artwork remain under their respective terms. Skill installation uses the independent [Skills CLI](https://github.com/vercel-labs/skills).
