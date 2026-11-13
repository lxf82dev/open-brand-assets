import argparse
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('logos', ROOT / 'skills/find-brand-logo/scripts/logos.py')
logos = importlib.util.module_from_spec(spec)
spec.loader.exec_module(logos)

class LogoTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.args = argparse.Namespace(cache_dir=str(self.directory / 'cache'), refresh=False, offline=False,
            source='all', query='OpenRouter', limit=2, json=True)

    def test_local_alias_and_real_download(self):
        self.args.offline = True
        self.args.query = 'BFL'
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(logos.search(self.args), 0)
        result = json.loads(out.getvalue())
        self.assertEqual(result['results'][0]['id'], 'black-forest-labs')
        self.args.brand = 'openrouter'
        self.args.variant = 'glyph-ink'
        self.args.output = str(self.directory / 'mark.svg')
        self.args.force = False
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(logos.fetch(self.args), 0)
        expected = ROOT / 'brands/openrouter/glyph-ink.svg'
        self.assertEqual(Path(self.args.output).read_bytes(), expected.read_bytes())
        with self.assertRaises(FileExistsError):
            logos.fetch(self.args)

    def test_local_png_search_metadata_drives_a_valid_download(self):
        self.args.offline = True
        self.args.query = 'Higgsfield'
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(logos.search(self.args), 0)
        item = next(row for row in json.loads(out.getvalue())['results'] if row['variant'] == 'site-icon')
        self.assertEqual(item['format'], 'png')
        self.args.brand, self.args.variant = item['id'], item['variant']
        self.args.output = str(self.directory / ('higgsfield.' + item['format']))
        self.args.force = False
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(logos.fetch(self.args), 0)
        self.assertTrue(Path(self.args.output).read_bytes().startswith(b'\x89PNG\r\n\x1a\n'))

    def test_checksum_mismatch_does_not_write(self):
        catalog = json.loads((ROOT / 'catalog.json').read_text())
        catalog = copy.deepcopy(catalog)
        brand = next(b for b in catalog['brands'] if b['id'] == 'openrouter')
        brand['assets'][0]['sha256'] = '0' * 64
        self.args.brand, self.args.variant = brand['id'], brand['assets'][0]['id']
        self.args.output, self.args.force = str(self.directory / 'output.svg'), False
        with patch.object(logos, 'local_catalog', return_value=(catalog, 'test', False)):
            with self.assertRaisesRegex(ValueError, 'Checksum mismatch'):
                logos.fetch(self.args)
        self.assertFalse(Path(self.args.output).exists())

    def test_standalone_skill_uses_remote_catalog(self):
        with patch.object(logos, 'LOCAL_ROOT', self.directory), patch.object(logos, 'get_json', return_value=({'brands': []}, 'now', False)) as get:
            logos.local_catalog(self.args.cache_dir)
            self.assertEqual(get.call_args.args[0], logos.RAW + 'catalog.json')
            with self.assertRaisesRegex(ValueError, 'Offline mode requires'):
                logos.local_catalog(self.args.cache_dir, offline=True)

    def test_partial_failure_retains_other_results(self):
        def adapter(source, args):
            if source == 'lobe':
                raise OSError('upstream unavailable')
            return [logos.row(source, 'OpenRouter', 'glyph', 'https://example.com/icon.svg')], {'checked_at': 'test'}
        with patch.object(logos, 'source_rows', side_effect=adapter), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(logos.search(self.args), 0)
        result = json.loads(out.getvalue())
        self.assertEqual(len(result['results']), len(logos.SOURCES) - 1)
        self.assertEqual(result['errors'], {'lobe': 'upstream unavailable'})

    def test_total_failure_returns_failure(self):
        with patch.object(logos, 'source_rows', side_effect=OSError('offline')), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(logos.search(self.args), 1)
        self.assertEqual(len(json.loads(out.getvalue())['errors']), len(logos.SOURCES))

    def test_new_source_layouts_metadata_and_pinned_urls(self):
        fixture = {'sha': 'fixed-revision', 'truncated': False, 'tree': [
            {'path': 'logos/react.svg', 'type': 'blob'},
            {'path': 'src/content/logos/github/github-icon.svg', 'type': 'blob'},
            {'path': 'public/images/about/not-a-brand.svg', 'type': 'blob'},
            {'path': 'icons/aarch64/aarch64-original.svg', 'type': 'blob'},
            {'path': 'svg/nextcloud-light.svg', 'type': 'blob'},
            {'path': 'svg/color/btc.svg', 'type': 'blob'},
            {'path': 'originals/btc.svg', 'type': 'blob'},
        ]}
        cases = [
            ('gilbarbara', [{'name': 'React', 'shortname': 'reactjs', 'files': ['react.svg'], 'url': 'https://react.dev'}], 'React', 'reactjs'),
            ('vectorlogozone', [], 'github', 'github'),
            ('devicon', [{'name': 'aarch64', 'altnames': ['arm64']}], 'aarch64', 'arm64'),
            ('selfhst', [{'Name': 'Nextcloud', 'Reference': 'nextcloud'}], 'Nextcloud', 'nextcloud'),
            ('dashboard-icons', [], 'nextcloud', 'nextcloud'),
            ('crypto', [{'symbol': 'BTC', 'name': 'Bitcoin'}], 'Bitcoin', 'btc'),
        ]
        for source, records, expected, query in cases:
            calls = []
            def get(url, *args):
                calls.append(url)
                return (fixture if '/git/trees/' in url else records), 'now', False
            with self.subTest(source=source), patch.object(logos, 'get_json', side_effect=get):
                rows, report = logos.source_rows(source, self.args)
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]['brand'], expected)
                self.assertEqual(logos.rank(rows[0], logos.normalize(query)), 0)
                self.assertIn('/fixed-revision/', rows[0]['url'])
                self.assertIn('/fixed-revision/', rows[0]['license_url'])
                self.assertEqual(report['revision'], 'fixed-revision')
                if len(calls) == 2:
                    self.assertIn('/fixed-revision/', calls[1])
                if source == 'vectorlogozone':
                    self.assertIn('website code', rows[0]['rights_note'])
                if source == 'selfhst':
                    self.assertIn('CC-BY-4.0', rows[0]['attribution'])

    def test_service_sources_include_png_only_fallback_without_duplicates(self):
        fixture = {'sha': 'fixed', 'truncated': False, 'tree': [
            {'path': 'svg/example.svg', 'type': 'blob'},
            {'path': 'png/example.png', 'type': 'blob'},
            {'path': 'png/raster-only.png', 'type': 'blob'},
            {'path': 'webp/raster-only.webp', 'type': 'blob'},
        ]}
        for source in ('selfhst', 'dashboard-icons'):
            with self.subTest(source=source), patch.object(logos, 'get_json', side_effect=lambda url, *args: (fixture if '/git/trees/' in url else [], 'now', False)):
                rows, _ = logos.source_rows(source, self.args)
                self.assertEqual(len(rows), 2)
                self.assertEqual({r['format'] for r in rows}, {'svg', 'png'})
                self.assertFalse(any('/png/example.png' in r['url'] for r in rows))

    def test_crypto_symbol_url_is_escaped_and_searchable_by_name(self):
        fixture = {'sha': 'fixed', 'truncated': False, 'tree': [{'path': 'svg/color/$pac.svg', 'type': 'blob'}]}
        with patch.object(logos, 'get_json', side_effect=[(fixture, 'now', False), ([{'name': 'PACcoin', 'symbol': '$PAC'}], 'now', False)]):
            rows, _ = logos.source_rows('crypto', self.args)
        self.assertIn('/%24pac.svg', rows[0]['url'])
        self.assertEqual(logos.rank(rows[0], 'paccoin'), 0)

    def test_unreadable_metadata_is_reported_as_source_failure(self):
        fixture = {'sha': 'fixed', 'truncated': False, 'tree': []}
        self.args.source = 'crypto'
        with patch.object(logos, 'get_json', side_effect=[(fixture, 'now', False), ({'unexpected': 'shape'}, 'now', False)]), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(logos.search(self.args), 1)
        result = json.loads(out.getvalue())
        self.assertEqual(set(result['errors']), {'crypto'})
        self.assertEqual(result['sources'], {})

    def test_plain_text_retains_required_attribution_and_rights_notes(self):
        self.args.json = False
        self.args.source = 'selfhst'
        item = logos.row('selfhst', 'OpenRouter', 'default', 'https://example.com/icon.svg',
                         attribution='CC-BY-4.0 selfh.st contributors', rights_note='Brand rights remain separate')
        with patch.object(logos, 'source_rows', return_value=([item], {'checked_at': 'now'})), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(logos.search(self.args), 0)
        self.assertIn('Attribution: CC-BY-4.0 selfh.st contributors', out.getvalue())
        self.assertIn('Rights: Brand rights remain separate', out.getvalue())

    def test_svgl_variants_and_brand_guidelines(self):
        self.args.source = 'svgl'
        data = [{'title': 'Example', 'route': {'light': 'https://svgl.app/library/a.svg', 'dark': 'https://svgl.app/library/b.svg'},
                 'wordmark': 'https://svgl.app/library/wordmark.svg', 'brandUrl': 'https://example.com/brand'}]
        with patch.object(logos, 'get_json', return_value=(data, 'now', False)):
            rows, _ = logos.source_rows('svgl', self.args)
        self.assertEqual({r['variant'] for r in rows}, {'route-light', 'route-dark', 'wordmark-default'})
        self.assertTrue(all(r['guidelines'] == 'https://example.com/brand' for r in rows))

    def test_github_adapters_use_existing_paths_at_pinned_commit(self):
        fixture = {'sha': 'abc123', 'truncated': False, 'tree': [
            {'path': 'packages/static-svg/icons/claude-color.svg', 'type': 'blob'},
            {'path': 'icons/github.svg', 'type': 'blob'},
            {'path': 'public/icons/openrouter/dark.svg', 'type': 'blob'},
            {'path': 'public/icons/openrouter', 'type': 'tree'},
            {'path': 'README.md', 'type': 'blob'}]}
        for source, expected in [('lobe', 'claude'), ('simple-icons', 'github'), ('thesvg', 'openrouter')]:
            with self.subTest(source=source), patch.object(logos, 'get_json', return_value=(fixture, 'now', False)):
                rows, _ = logos.source_rows(source, self.args)
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]['brand'], expected)
                self.assertIn('/abc123/', rows[0]['url'])

    def test_truncated_github_tree_is_an_error(self):
        with patch.object(logos, 'get_json', return_value=({'truncated': True}, 'now', False)):
            with self.assertRaisesRegex(ValueError, 'truncated'):
                logos.source_rows('lobe', self.args)

    def test_cache_refresh_and_expired_failure(self):
        url = 'https://example.com/catalog'
        with patch.object(logos, 'request_bytes', return_value=b'{"ok": true}') as fetch:
            self.assertFalse(logos.get_json(url, self.args.cache_dir)[2])
            self.assertTrue(logos.get_json(url, self.args.cache_dir)[2])
            self.assertFalse(logos.get_json(url, self.args.cache_dir, refresh=True)[2])
            self.assertEqual(fetch.call_count, 2)
        cache = next(Path(self.args.cache_dir).glob('*.json'))
        data = json.loads(cache.read_text())
        data['timestamp'] = 0
        cache.write_text(json.dumps(data))
        with patch.object(logos, 'request_bytes', side_effect=OSError('unavailable')):
            with self.assertRaises(OSError):
                logos.get_json(url, self.args.cache_dir)

    def test_svg_checks_allow_real_embedded_png_and_reject_active_content(self):
        for svg in ('<script/>', '<foreignObject/>', '<image href="https://example.com/image.png"/>',
                    '<path onclick="go()"/>', '<style>@import "https://example.com/style";</style>',
                    '<path style="fill:url(https://example.com/x)"/>', '<image href="data:image/svg+xml;base64,xxx"/>'):
            with self.subTest(svg=svg), self.assertRaises(ValueError):
                logos.check_image(f'<svg xmlns="http://www.w3.org/2000/svg">{svg}</svg>'.encode(), '.svg')
        actual = ROOT / 'brands/heygen/heygen-symbol-black-logo.svg'
        logos.check_image(actual.read_bytes(), '.svg')

    def test_all_committed_manifests_and_asset_hashes(self):
        spec = importlib.util.spec_from_file_location('catalog_builder', ROOT / 'scripts/catalog.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.build(), json.loads((ROOT / 'catalog.json').read_text()))

    def test_validator_rejects_tampered_asset(self):
        spec = importlib.util.spec_from_file_location('catalog_builder', ROOT / 'scripts/catalog.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        shutil.copytree(ROOT / 'brands/openrouter', self.directory / 'brands/openrouter')
        (self.directory / 'brands/openrouter/glyph-ink.svg').write_bytes(b'tampered')
        with patch.object(module, 'ROOT', self.directory):
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                module.build()

if __name__ == '__main__':
    unittest.main()
