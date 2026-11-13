#!/usr/bin/env python3
"""Validate brand manifests and build the public catalog. No dependencies."""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('logo_cli', ROOT / 'skills/find-brand-logo/scripts/logos.py')
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)

def require(condition, message):
    if not condition:
        raise ValueError(message)

def text(value):
    return isinstance(value, str) and bool(value.strip())

def url(value):
    parsed = urllib.parse.urlparse(value) if isinstance(value, str) else None
    return parsed is not None and parsed.scheme == 'https' and bool(parsed.hostname) and not parsed.username and not parsed.password

def date(value):
    return isinstance(value, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', value) and dt.date.fromisoformat(value) <= dt.datetime.now(dt.timezone.utc).date()

def build():
    brands, files = [], set()
    for manifest in sorted((ROOT / 'brands').glob('*/brand.json')):
        brand = json.loads(manifest.read_text())
        slug = brand.get('id', '')
        require(bool(re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug)) and slug == manifest.parent.name, f'{manifest}: invalid brand id')
        require(text(brand.get('name')) and url(brand.get('website')), f'{slug}: name and HTTPS website required')
        require(isinstance(brand.get('aliases'), list) and all(text(a) for a in brand['aliases']), f'{slug}: aliases must be text strings')
        require(isinstance(brand.get('categories'), list) and len(brand['categories']) > 0 and all(text(a) for a in brand['categories']), f'{slug}: categories required')
        usage = brand.get('usage', {})
        require(usage.get('status') in ('guidelines-available', 'permission-required', 'unverified', 'owner-supplied'), f'{slug}: invalid usage status')
        require(usage.get('guidelines') is None or url(usage['guidelines']), f'{slug}: invalid guideline URL')
        require(text(usage.get('note')) and date(usage.get('checked')), f'{slug}: dated usage notes required')
        require(isinstance(brand.get('assets'), list) and len(brand['assets']) > 0, f'{slug}: assets required')
        variants = set()
        for asset in brand['assets']:
            variant = asset.get('id', '')
            require(bool(re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', variant)) and variant not in variants, f'{slug}: invalid or duplicate variant {variant}')
            variants.add(variant)
            relative = Path(asset.get('file', ''))
            require(relative.parts[:2] == ('brands', slug) and len(relative.parts) == 3 and '..' not in relative.parts, f'{slug}: invalid asset path')
            path = ROOT / relative
            require(not path.is_symlink() and path.is_file(), f'{slug}: missing asset {relative}')
            require(asset.get('format') in ('svg', 'png') and path.suffix == '.' + asset['format'], f'{slug}: invalid file format')
            require(asset.get('role') in ('symbol', 'wordmark', 'lockup', 'site-icon', 'app-icon'), f'{slug}: invalid role')
            require(asset.get('theme') in ('light', 'dark', 'any'), f'{slug}: invalid theme')
            data = path.read_bytes()
            require(0 < len(data) <= 5 * 1024 * 1024, f'{slug}: asset must be 1 byte to 5 MiB')
            require(hashlib.sha256(data).hexdigest() == asset.get('sha256'), f'{slug}: checksum mismatch for {relative}')
            try:
                cli.check_image(data, path.suffix)
            except ValueError as exc:
                raise ValueError(f'{relative}: {exc}') from exc
            source = asset.get('source', {})
            require(source.get('kind') in ('official-brand-kit', 'official-website', 'owner-supplied', 'upstream-library'), f'{slug}: invalid source kind')
            require(url(source.get('page')) and url(source.get('url')) and date(source.get('retrieved')), f'{slug}: dated HTTPS source URLs required')
            require(text(source.get('modifications')), f'{slug}: record modifications explicitly')
            require(text(asset.get('rights', {}).get('license')) and text(asset['rights'].get('note')), f'{slug}: rights metadata required')
            files.add(relative.as_posix())
        brands.append(brand)
    require(bool(brands), 'No brands found')
    actual = {p.relative_to(ROOT).as_posix() for p in (ROOT / 'brands').rglob('*') if p.is_file() and p.suffix in ('.svg', '.png')}
    require(actual == files, f'Orphan or missing files: {sorted(actual ^ files)}')
    return {'schema_version': 1, 'repository': 'https://github.com/lxf82dev/open-brand-assets', 'brands': brands}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail if catalog.json needs regeneration')
    args = parser.parse_args()
    try:
        catalog = build()
        output = json.dumps(catalog, indent=2, ensure_ascii=False) + '\n'
        target = ROOT / 'catalog.json'
        if args.check:
            require(target.exists() and target.read_text() == output, 'catalog.json is stale. Run python3 scripts/catalog.py')
        else:
            target.write_text(output)
        print(f"Validated {len(catalog['brands'])} brands / {sum(len(b['assets']) for b in catalog['brands'])} assets")
        return 0
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
