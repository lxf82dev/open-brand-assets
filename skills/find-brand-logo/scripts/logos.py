#!/usr/bin/env python3
"""Search complementary and upstream brand catalogs. Python 3.10+, no packages."""
import argparse
import base64
import concurrent.futures
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

REPO = 'lxf82dev/open-brand-assets'
RAW = f'https://raw.githubusercontent.com/{REPO}/main/'
LOCAL_ROOT = Path(__file__).resolve().parents[3]
GITHUB_SOURCES = {
    'lobe': ('lobehub/lobe-icons', 'master', 'MIT', 'LICENSE', None),
    'simple-icons': ('simple-icons/simple-icons', 'develop', 'CC0-1.0', 'LICENSE.md', None),
    'thesvg': ('glincker/thesvg', 'main', 'MIT', 'LICENSE', None),
    'gilbarbara': ('gilbarbara/logos', 'main', 'CC0-1.0', 'LICENSE.txt', 'logos.json'),
    'vectorlogozone': ('VectorLogoZone/vectorlogozone', 'main', 'AGPL-3.0', 'LICENSE.txt', None),
    'devicon': ('devicons/devicon', 'master', 'MIT', 'LICENSE', 'devicon.json'),
    'selfhst': ('selfhst/icons', 'main', 'CC-BY-4.0', 'LICENSE', 'index.json'),
    'dashboard-icons': ('homarr-labs/dashboard-icons', 'main', 'Apache-2.0', 'LICENSE', None),
    'crypto': ('spothq/cryptocurrency-icons', 'master', 'CC0-1.0', 'LICENSE.md', 'manifest.json'),
}
SOURCES = ('ours', 'svgl', *GITHUB_SOURCES)
MAX_BYTES = 32 * 1024 * 1024

def normalize(value):
    value = unicodedata.normalize('NFKD', value).casefold()
    return re.sub(r'[^a-z0-9]', '', value)

def request_bytes(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Expected a public HTTPS source URL')
    req = urllib.request.Request(url, headers={'User-Agent': f'open-brand-assets/1.0 (+https://github.com/{REPO})'})
    with urllib.request.urlopen(req, timeout=30) as response:
        if urllib.parse.urlparse(response.url).scheme != 'https':
            raise ValueError('Refusing an insecure redirect')
        body = response.read(MAX_BYTES + 1)
    if len(body) > MAX_BYTES:
        raise ValueError('Response exceeds 32 MiB')
    return body

def get_json(url, cache_dir, refresh=False):
    path = Path(cache_dir) / (hashlib.sha256(url.encode()).hexdigest() + '.json')
    if not refresh and path.exists():
        try:
            saved = json.loads(path.read_text())
            if 0 <= time.time() - saved['timestamp'] < 86400:
                return saved['data'], saved['checked_at'], True
        except (ValueError, KeyError, TypeError, OSError):
            pass
    data = json.loads(request_bytes(url))
    checked = dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    path.parent.mkdir(parents=True, exist_ok=True)
    saved = {'timestamp': time.time(), 'checked_at': checked, 'data': data}
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False) as file:
        json.dump(saved, file)
        temporary = file.name
    os.replace(temporary, path)
    return data, checked, False

def local_catalog(cache_dir, refresh=False, offline=False):
    path = LOCAL_ROOT / 'catalog.json'
    if path.exists():
        return json.loads(path.read_text()), 'local checkout', False
    if offline:
        raise ValueError('Offline mode requires a repository checkout with catalog.json')
    return get_json(RAW + 'catalog.json', cache_dir, refresh)

def row(source, brand, variant, url, **extra):
    return {'source': source, 'brand': brand, 'variant': variant, 'url': url, **extra}

def variants(value):
    if isinstance(value, str):
        return [('default', value)]
    if isinstance(value, dict):
        return [(key, val) for key, val in value.items() if isinstance(val, str)]
    return []

def source_rows(source, args):
    if source == 'ours':
        catalog, checked, cached = local_catalog(args.cache_dir, args.refresh, args.offline)
        rows = []
        for brand in catalog['brands']:
            for asset in brand['assets']:
                rows.append(row(source, brand['name'], asset['id'], RAW + asset['file'], id=brand['id'],
                    aliases=brand['aliases'], role=asset['role'], theme=asset['theme'],
                    sha256=asset['sha256'], file=asset['file'], provenance=asset['source'],
                    usage=brand['usage'], license=asset['rights']['license'], note=asset.get('note')))
        return rows, {'checked_at': checked, 'cached': cached}
    if source == 'svgl':
        data, checked, cached = get_json('https://api.svgl.app/', args.cache_dir, args.refresh)
        if not isinstance(data, list):
            raise ValueError('SVGL response must be a catalog array')
        rows = []
        for brand in data:
            for field in ('route', 'wordmark'):
                for variant, url in variants(brand.get(field)):
                    rows.append(row(source, brand['title'], f'{field}-{variant}', url,
                        website=brand.get('url'), guidelines=brand.get('brandUrl'),
                        library_license='MIT', usage_status='check-brand-guidelines'))
        return rows, {'checked_at': checked, 'cached': cached}
    repo, branch, license_id, license_file, metadata_file = GITHUB_SOURCES[source]
    tree, checked, cached = get_json(f'https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1', args.cache_dir, args.refresh)
    if tree.get('truncated'):
        raise ValueError('Upstream tree is truncated; use the upstream search directly')
    revision = tree['sha']
    raw_base = f'https://raw.githubusercontent.com/{repo}/{revision}/'
    metadata = {}
    if metadata_file:
        records, _, _ = get_json(raw_base + metadata_file, args.cache_dir, args.refresh)
        if not isinstance(records, list) or not all(isinstance(record, dict) for record in records):
            raise ValueError(f'{source} metadata must be an array of records')
        for record in records:
            if source == 'gilbarbara':
                for filename in record.get('files', []):
                    metadata[filename] = record
            else:
                key = record.get({'devicon': 'name', 'selfhst': 'Reference', 'crypto': 'symbol'}[source])
                if isinstance(key, str):
                    metadata[key.casefold()] = record
    paths = {item['path'] for item in tree['tree'] if item.get('type') == 'blob'}
    rows = []
    for item in tree['tree']:
        path = item['path']
        extension = Path(path).suffix.lower()
        if item.get('type') != 'blob' or extension not in ('.svg', '.png'):
            continue
        parts = path.split('/')
        if extension == '.png':
            # These collections include PNG-only services. Prefer SVG when supplied.
            if source not in ('selfhst', 'dashboard-icons') or len(parts) != 2 or parts[0] != 'png':
                continue
            if 'svg/' + Path(path).stem + '.svg' in paths:
                continue
        extra = {}
        if source == 'lobe' and path.startswith('packages/static-svg/icons/'):
            name = parts[-1][:-4]
            brand = re.sub(r'-(color|text|brand|text-cn|text-en)$', '', name)
            variant = name
        elif source == 'simple-icons' and len(parts) == 2 and parts[0] == 'icons':
            brand, variant = parts[-1][:-4], 'mono'
        elif source == 'thesvg' and len(parts) == 4 and parts[:2] == ['public', 'icons']:
            brand, variant = parts[2], parts[3][:-4]
        elif source == 'gilbarbara' and len(parts) == 2 and parts[0] == 'logos':
            record = metadata.get(parts[1], {})
            brand = record.get('name') or re.sub(r'-(icon|wordmark|dark|light|mono)(?:-.*)?$', '', Path(path).stem)
            variant = Path(path).stem
            extra = {'aliases': [record['shortname']] if record.get('shortname') else [], 'website': record.get('url')}
        elif source == 'vectorlogozone' and len(parts) == 5 and parts[:3] == ['src', 'content', 'logos']:
            brand, variant = parts[3], Path(path).stem
            extra = {'rights_note': 'AGPL-3.0 covers the website code; logos remain their owners\' property. Upstream places its modifications in the public domain. See the upstream README.'}
        elif source == 'devicon' and len(parts) == 3 and parts[0] == 'icons':
            brand, variant = parts[1], Path(path).stem
            extra = {'aliases': metadata.get(brand.casefold(), {}).get('altnames', [])}
        elif source in ('selfhst', 'dashboard-icons') and len(parts) == 2 and parts[0] in ('svg', 'png'):
            stem = Path(path).stem
            reference = re.sub(r'-(dark|light)$', '', stem)
            brand = metadata.get(reference.casefold(), {}).get('Name') or reference
            variant = stem + ('-png' if extension == '.png' else '')
            extra = {'aliases': [reference]}
            if source == 'selfhst':
                extra['attribution'] = 'selfh.st Icons contributors — https://github.com/selfhst/icons (CC-BY-4.0 collection; brand rights remain separate)'
        elif source == 'crypto' and len(parts) == 3 and parts[0] == 'svg' and parts[1] in ('black', 'color', 'icon', 'white'):
            symbol = Path(path).stem
            brand = metadata.get(symbol.casefold(), {}).get('name') or symbol
            variant = parts[1]
            extra = {'aliases': [symbol], 'symbol': symbol}
        else:
            continue
        if source in ('lobe', 'simple-icons', 'thesvg'):
            extra['library_license'] = license_id
        rows.append(row(source, brand, variant, raw_base + urllib.parse.quote(path, safe='/'),
            repository=f'https://github.com/{repo}', revision=revision,
            repository_license=license_id, license_url=raw_base + license_file, format=extension[1:],
            usage_status='check-brand-guidelines', **extra))
    return rows, {'checked_at': checked, 'cached': cached, 'revision': revision}

def rank(item, query):
    terms = [normalize(item['brand']), normalize(item.get('id', ''))]
    terms += [normalize(alias) for alias in item.get('aliases', [])]
    if query in terms:
        return 0
    if any(term.startswith(query) for term in terms if term):
        return 1
    if any(query in term for term in terms if term):
        return 2
    return None

def search(args):
    selected = ['ours'] if args.offline else list(SOURCES) if args.source == 'all' else [args.source]
    query = normalize(args.query)
    if not query:
        raise ValueError('Search needs at least one letter or digit')
    found, reports, errors = [], {}, {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(6, len(selected))) as pool:
        pending = {pool.submit(source_rows, source, args): source for source in selected}
        for future in concurrent.futures.as_completed(pending):
            source = pending[future]
            try:
                rows, report = future.result()
                hits = [(rank(item, query), item) for item in rows]
                hits = [(score, item) for score, item in hits if score is not None]
                hits.sort(key=lambda pair: (pair[0], pair[1]['brand'].casefold(), pair[1]['variant']))
                found.extend(item for _, item in hits[:args.limit])
                reports[source] = {**report, 'matches': len(hits)}
            except Exception as exc:
                errors[source] = str(exc)
    found.sort(key=lambda item: (rank(item, query), SOURCES.index(item['source']), item['brand'], item['variant']))
    result = {'query': args.query, 'results': found, 'sources': reports, 'errors': errors}
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        for item in found:
            print(f"[{item['source']}] {item['brand']} / {item['variant']}\n  {item['url']}")
            if item.get('usage'):
                print(f"  Usage: {item['usage']['status']} — {item['usage']['note']}")
            if item.get('attribution'):
                print(f"  Attribution: {item['attribution']}")
            if item.get('rights_note'):
                print(f"  Rights: {item['rights_note']}")
        for source, error in errors.items():
            print(f'Warning: {source}: {error}', file=sys.stderr)
        if not found:
            print('No matches in the sources checked. Try an alias or the official brand site.')
    return 1 if len(errors) == len(selected) else 0

def check_image(data, suffix):
    if suffix == '.png':
        if not data.startswith(b'\x89PNG\r\n\x1a\n'):
            raise ValueError('Expected PNG bytes')
    elif suffix == '.svg':
        if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
            raise ValueError('SVG declarations are unsupported')
        root = ET.fromstring(data)
        if root.tag != '{http://www.w3.org/2000/svg}svg':
            raise ValueError('Expected SVG root with its namespace')
        for element in root.iter():
            tag = element.tag.rsplit('}', 1)[-1].lower()
            if tag in ('script', 'foreignobject', 'iframe', 'object', 'embed'):
                raise ValueError('Active SVG content is unsupported')
            for key, value in element.attrib.items():
                attr = key.rsplit('}', 1)[-1].lower()
                raster = value.startswith('data:image/png;base64,') and tag == 'image' and attr == 'href'
                if raster:
                    embedded = base64.b64decode(re.sub(r'\s', '', value.split(',', 1)[1]), validate=True)
                    if not embedded.startswith(b'\x89PNG\r\n\x1a\n'):
                        raise ValueError('Invalid embedded PNG')
                if attr.startswith('on') or (attr in ('href', 'src') and not value.startswith('#') and not raster):
                    raise ValueError('Active or external SVG references are unsupported')
            css = ' '.join(element.attrib.values()) + (element.text or '')
            if re.search(r'@import|javascript:|expression\s*\(', css, re.I):
                raise ValueError('Active SVG CSS is unsupported')
            for target in re.findall(r'url\s*\(([^)]*)\)', css, re.I):
                if not target.strip(' \"\x27').startswith('#'):
                    raise ValueError('External SVG CSS references are unsupported')
    else:
        raise ValueError('Only .svg and .png outputs are supported')

def fetch(args):
    catalog, _, _ = local_catalog(args.cache_dir, args.refresh, args.offline)
    brand = next((b for b in catalog['brands'] if args.brand in (b['id'], b['name'], *b['aliases'])), None)
    if not brand:
        raise ValueError('Unknown local brand. Search all sources for upstream candidates.')
    asset = next((a for a in brand['assets'] if a['id'] == args.variant), None)
    if not asset:
        raise ValueError('Choose a variant: ' + ', '.join(a['id'] for a in brand['assets']))
    relative = Path(asset['file'])
    if relative.is_absolute() or '..' in relative.parts or relative.parts[:1] != ('brands',):
        raise ValueError('Invalid catalog asset path')
    local = LOCAL_ROOT / relative
    if local.is_file():
        data = local.read_bytes()
    elif args.offline:
        raise ValueError('Asset is unavailable in the offline checkout')
    else:
        data = request_bytes(RAW + asset['file'])
    if hashlib.sha256(data).hexdigest() != asset['sha256']:
        raise ValueError('Checksum mismatch. Refresh the catalog or inspect the source.')
    destination = Path(args.output)
    if destination.suffix.lower() != '.' + asset['format']:
        raise ValueError('Output extension must match the catalog format')
    check_image(data, destination.suffix.lower())
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('wb' if args.force else 'xb') as file:
        file.write(data)
    print(json.dumps({'output': str(destination.resolve()), 'sha256': asset['sha256'],
                      'provenance': asset['source'], 'usage': brand['usage']}, indent=2))
    return 0

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ('search', 'fetch'):
        child = sub.add_parser(command)
        child.add_argument('--cache-dir', default=str(Path(os.getenv('XDG_CACHE_HOME', Path.home() / '.cache')) / 'open-brand-assets'))
        child.add_argument('--refresh', action='store_true', help='Bypass the 24-hour public catalog cache')
        child.add_argument('--offline', action='store_true', help='Use only this checkout; no network requests')
        if command == 'search':
            child.add_argument('query')
            child.add_argument('--source', choices=(*SOURCES, 'all'), default='all')
            child.add_argument('--limit', type=int, default=10, help='Maximum results per source (1–100)')
            child.add_argument('--json', action='store_true')
        else:
            child.add_argument('brand')
            child.add_argument('--variant', required=True)
            child.add_argument('--output', required=True, help='Exact SVG or PNG destination filename')
            child.add_argument('--force', action='store_true', help='Replace an existing destination')
    args = parser.parse_args(argv)
    if args.command == 'search' and not 1 <= args.limit <= 100:
        parser.error('--limit must be between 1 and 100')
    try:
        return search(args) if args.command == 'search' else fetch(args)
    except Exception as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
