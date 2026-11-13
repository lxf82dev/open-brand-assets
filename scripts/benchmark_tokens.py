#!/usr/bin/env python3
"""Count context text for a fixed three-logo lookup; optional tiktoken dependency.

This measures text payloads, not an agent run, bill, latency, or universal saving.
"""
import argparse
import datetime as dt
import hashlib
from html.parser import HTMLParser
import importlib.metadata
import json
from pathlib import Path
import re
import subprocess
import tempfile
import urllib.parse
import urllib.request

TASKS = (
    ('heygen', 'HeyGen', 'https://www.heygen.com/brand-kit'),
    ('black-forest-labs', 'BFL', 'https://bfl.ai/brand'),
    ('openrouter', 'OpenRouter', 'https://openrouter.ai/brand'),
)
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
SKIP = {'script', 'style', 'noscript', 'svg', 'nav', 'header', 'footer', 'template'}

class ReadablePage(HTMLParser):
    """Extract main/body text and unique downloadable asset links, not raw HTML."""
    def __init__(self, base, main_only):
        super().__init__(convert_charrefs=True)
        self.base, self.main_only = base, main_only
        self.stack, self.text, self.links = [], [], []

    def active(self):
        return not any(tag in SKIP for tag in self.stack) and ('main' in self.stack if self.main_only else 'body' in self.stack)

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)
        if self.active():
            attributes = dict(attrs)
            for key in ('href', 'src'):
                value = attributes.get(key, '')
                url = urllib.parse.urljoin(self.base, value)
                if urllib.parse.urlparse(url).path.lower().endswith(('.svg', '.png', '.zip')) and url not in self.links:
                    self.links.append(url)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag in self.stack:
            index = len(self.stack) - 1 - self.stack[::-1].index(tag)
            del self.stack[index:]

    def handle_data(self, data):
        value = ' '.join(data.split())
        if self.active() and value:
            self.text.append(value)

    def payload(self):
        return '\n'.join(self.text) + '\n\nDownloadable asset URLs\n' + '\n'.join(self.links) + '\n'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path, default=Path('research/token-benchmark.json'))
    parser.add_argument('--snapshots', type=Path, help='Optional private directory of heygen.txt, bfl.txt, and openrouter.txt HTML snapshots')
    args = parser.parse_args()
    try:
        import tiktoken
    except ImportError:
        parser.error('For this optional benchmark only: python3 -m pip install tiktoken==0.12.0')
    encoding = tiktoken.get_encoding('o200k_base')
    count = lambda text: len(encoding.encode(text, disallowed_special=()))
    root = args.root.resolve()
    instruction = (root / 'skills/find-brand-logo/SKILL.md').read_text()
    catalog = json.loads((root / 'catalog.json').read_text())
    source_pages, lookups, receipts = [], [], []
    with tempfile.TemporaryDirectory(prefix='logo-context-benchmark-') as temporary:
        for brand_id, query, url in TASKS:
            if args.snapshots:
                filename = 'bfl.txt' if brand_id == 'black-forest-labs' else brand_id + '.txt'
                raw = (args.snapshots / filename).read_bytes()
            else:
                request = urllib.request.Request(url, headers={'User-Agent': 'open-brand-assets-context-benchmark'})
                with urllib.request.urlopen(request, timeout=30) as response:
                    raw = response.read(8 * 1024 * 1024 + 1)
                if len(raw) > 8 * 1024 * 1024:
                    raise ValueError('Brand page exceeds the benchmark download limit')
            html = raw.decode('utf-8')
            page = ReadablePage(url, bool(re.search(r'<main(?:\s|>)', html, re.I)))
            page.feed(html)
            readable = page.payload()
            source_pages.append({'brand': brand_id, 'url': url, 'html_sha256': hashlib.sha256(raw).hexdigest(),
                'counted_text_sha256': hashlib.sha256(readable.encode()).hexdigest(), 'tokens': count(readable),
                'characters': len(readable), 'asset_links': len(page.links)})
            command = ['python3', 'logos.py', 'search', query, '--source', 'ours', '--limit', '1', '--offline']
            lookup = subprocess.run(command, cwd=root, capture_output=True, text=True, check=True).stdout
            lookups.append({'brand': brand_id, 'command': command, 'stdout_sha256': hashlib.sha256(lookup.encode()).hexdigest(), 'tokens': count(lookup)})
            brand = next(b for b in catalog['brands'] if b['id'] == brand_id)
            variant = sorted(brand['assets'], key=lambda asset: asset['id'])[0]
            destination = Path(temporary) / (brand_id + '.' + variant['format'])
            command = ['python3', 'logos.py', 'fetch', brand_id, '--variant', variant['id'], '--output', str(destination), '--offline']
            receipt = subprocess.run(command, cwd=root, capture_output=True, text=True, check=True).stdout
            # A fixed path keeps counts independent of the user's checkout/temp directory.
            record = json.loads(receipt)
            record['output'] = './public/logos/' + destination.name
            normalized = json.dumps(record, indent=2) + '\n'
            receipts.append({'brand': brand_id, 'variant': variant['id'], 'sha256': record['sha256'], 'tokens': count(normalized)})
    page_tokens = sum(p['tokens'] for p in source_pages)
    lookup_tokens = sum(p['tokens'] for p in lookups)
    receipt_tokens = sum(p['tokens'] for p in receipts)
    instructions = count(instruction)
    without = page_tokens + receipt_tokens
    with_skill = instructions + lookup_tokens + receipt_tokens
    report = {
        'measured_at': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
        'kind': 'controlled-context-payload-comparison-not-agent-billing',
        'task': 'Retrieve one supplied logo variant each for HeyGen, Black Forest Labs, and OpenRouter, retaining source/hash receipts.',
        'tokenizer': {'package': 'tiktoken', 'version': importlib.metadata.version('tiktoken'), 'encoding': 'o200k_base'},
        'root_commit': subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=root, capture_output=True, text=True, check=True).stdout.strip(),
        'working_tree_dirty': bool(subprocess.run(['git', 'status', '--porcelain'], cwd=root, capture_output=True, text=True, check=True).stdout.strip()),
        'cli_sha256': hashlib.sha256((root / 'skills/find-brand-logo/scripts/logos.py').read_bytes()).hexdigest(),
        'inputs': {'pages': source_pages, 'lookups': lookups, 'receipts': receipts,
            'skill_instructions': {'tokens': instructions, 'sha256': hashlib.sha256(instruction.encode()).hexdigest()}},
        'totals': {'without_skill_page_reading': without, 'with_skill_targeted_lookup': with_skill,
            'difference': without - with_skill, 'reduction_percent': round((1 - with_skill / without) * 100, 1)},
        'method': [
            'Baseline: official page main/body text plus deduplicated SVG/PNG/ZIP URLs; excludes scripts, styles, SVG markup, navigation, header, footer, and raw HTML.',
            'Skill: complete SKILL.md loaded once plus plain-text search --source ours --limit 1 output for each known brand.',
            'Both totals include identical normalized fetch source/hash/usage receipts for the same three delivered variants.',
            'Counts are sums of separately tokenized text payloads, not provider request usage. Asset bytes stay on disk in both scenarios.',
            'Does not measure model reasoning/output, chat/tool envelopes, installation, visual inspection, policy review, network latency, or API billing.',
            'Baseline URLs and local brand coverage are known in advance. Shorter page extraction or custom scripted lookup can match or beat the skill. Broad searches and full JSON output use more context.',
            'Official pages can change. Source-content hashes record this run; a future live run may produce different numbers. No third-party page text is redistributed in this report.',
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'report': str(args.output), 'totals': report['totals'], 'parts': {'page_text': page_tokens, 'skill_instructions': instructions, 'lookup_output': lookup_tokens, 'shared_receipts': receipt_tokens}}, indent=2))

if __name__ == '__main__':
    main()
