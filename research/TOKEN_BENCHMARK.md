# Token comparison methodology

This is a reproducible **context-text payload comparison**, not an autonomous-agent performance study, a provider usage report, or a guarantee of a particular cost saving.

## The task and baseline

Retrieve one supplied logo variant each for HeyGen, Black Forest Labs, and OpenRouter, keeping source/hash/usage receipts for the downloaded files. The three official brand-page URLs and our coverage of those brands are known beforehand.

The baseline counts readable text from those official pages plus unique downloadable SVG/PNG/ZIP URLs. The script chooses `<main>` when available, otherwise `<body>`, and excludes scripts, styles, SVG markup, navigation, headers, footers, noscript content, and templates. This is an HTML-text extraction rule, not a browser-rendered visibility audit. It does not count raw HTML or paste image contents into context.

The skill path counts the complete `skills/find-brand-logo/SKILL.md` once, plus the plain-text output of these targeted lookups:

```bash
python3 logos.py search HeyGen --source ours --limit 1 --offline
python3 logos.py search BFL --source ours --limit 1 --offline
python3 logos.py search OpenRouter --source ours --limit 1 --offline
```

The first alphabetically ordered variant returned for each brand is retrieved with the CLI's `fetch --offline`. The report records the exact variant and image SHA-256. Both scenarios include the **same** resulting source/hash/usage receipt texts, with output paths normalized to `./public/logos/<brand>.<format>` so temporary-directory names cannot affect the count. These shared receipts hold the delivered metadata constant; the baseline is not an independently executed browsing agent.

## Recorded result

Measured on **2026-11-13**, using `tiktoken==0.12.0` and `o200k_base`:

| Component | Tokens |
| --- | ---: |
| Three official pages, readable text and asset URLs | 3,399 |
| Complete skill instructions | 811 |
| Three targeted lookup outputs | 213 |
| Shared receipt output, counted on each side | 651 |
| Without skill: page reading + receipts | **4,050** |
| With skill: instructions + lookups + receipts | **1,675** |

The difference is **2,375 text tokens**, or **58.6%** of the baseline. Counts are summed across separately tokenized payloads. The [JSON report](token-benchmark.json) records page URLs, source-content hashes, the code commit, skill hash, commands, variants, and tokenizer version.

## Reproduce

From the repository root, in an isolated environment:

```bash
python3 -m venv /tmp/open-brand-assets-token-venv
/tmp/open-brand-assets-token-venv/bin/python -m pip install tiktoken==0.12.0
/tmp/open-brand-assets-token-venv/bin/python scripts/benchmark_tokens.py --output /tmp/open-brand-assets-token-benchmark.json
```

The optional script fetches the three official pages. The tokenizer may download its encoding on first use. It performs local searches and verified local copies into a temporary directory; it does not modify the collection or require a model API key. `tiktoken` is not a dependency of the logo CLI or skill. Third-party page text is not redistributed in the report. Use `--snapshots <private-directory>` with `heygen.txt`, `bfl.txt`, and `openrouter.txt` HTML files to remeasure privately retained inputs.

## Limits on interpretation

- No model agent was run on either path. These are measured text counts, not actual provider-billed input/output tokens.
- Reasoning and generated output, user/system prompts, chat/tool envelopes, installation, network latency, visual inspection, and further policy review are excluded. Fetch receipts are included equally; image bytes remain on disk.
- Exact URLs and local coverage are known. Discovery overhead is not included for either path.
- The baseline reads the extracted brand-page content. A targeted browser extraction, direct download, or custom script can be equally lean or leaner without this skill.
- Narrow, known-brand lookups are the measured configuration. Default broad searches, larger limits, full JSON output, and new brands can use more context. This does not establish a minimum achievable token count.
- `o200k_base` is one tokenizer, not a model-independent unit. Other coding agents and model families may count the same text differently. Context counts also do not directly establish monetary savings or prompt-cache discounts.
- Official pages can change. Future live runs may differ even when our code is unchanged. Source hashes identify the original inputs; the retained report does not claim immutable upstream content.
- The three brands and variants are an example, not a representative multi-brand evaluation. Usage notes do not replace checking official guidance when that is needed for the intended use.
