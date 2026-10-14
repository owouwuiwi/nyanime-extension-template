import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'website'


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        for name in ['href', 'src']:
            if values.get(name):
                self.links.append(values[name])


class WebsiteTest(unittest.TestCase):
    def test_internal_html_links_resolve_without_leaving_example(self):
        seen = 0
        for page in SITE.rglob('*.html'):
            parser = Links()
            parser.feed(page.read_text(encoding='utf-8'))
            base = 'https://fixture.invalid/example/' + page.relative_to(SITE).as_posix()
            for link in parser.links:
                target = urlparse(urljoin(base, link))
                if target.hostname != 'fixture.invalid':
                    continue
                if target.path == '/':
                    continue  # Shared Nyanime home branding.
                self.assertTrue(target.path.startswith('/example/'), (page, link))
                file = SITE / unquote(target.path.removeprefix('/example/'))
                if file.is_dir():
                    file /= 'index.html'
                # This file is produced only after the compilation checks finish.
                if file.name == 'placeholder-extension-kit.zip':
                    continue
                self.assertTrue(file.is_file(), (page, link, file))
                seen += 1
        self.assertGreater(seen, 200)

    def test_every_title_has_its_own_details_and_original_images(self):
        catalogue = json.loads((SITE / 'api/catalogue.json').read_text())
        for entry in catalogue['entries']:
            self.assertTrue((SITE / entry['url'] / 'index.html').is_file())
            self.assertTrue((SITE / entry['cover']).is_file())
            self.assertTrue((SITE / entry['banner']).is_file())
            self.assertGreater(entry['publishedAt'], 0)
            self.assertNotIn('catalogIds', entry)

    def test_original_media_have_usable_containers(self):
        for name in ['demo-180.mp4', 'demo-360.mp4', 'tv-test.mp4']:
            data = (SITE / 'media' / name).read_bytes()
            self.assertIn(b'ftyp', data[:32])
            self.assertLess(data.index(b'moov'), data.index(b'mdat'), 'MP4 must support progressive playback')
        self.assertTrue((SITE / 'media/demo-en.vtt').read_text().startswith('WEBVTT'))

    def test_story_navigation_starts_at_one_and_moves_forward(self):
        for medium, part in [('video', 'episode'), ('manga', 'chapter')]:
            first = (SITE / medium / 'demo-02' / (part + '-01') / 'index.html').read_text()
            last = (SITE / medium / 'demo-02' / (part + '-03') / 'index.html').read_text()
            self.assertNotIn('Previous ' + part, first)
            self.assertIn('Next ' + part, first)
            self.assertIn(part + '-02/', first)
            self.assertIn('Previous ' + part, last)
            self.assertNotIn('Next ' + part, last)


if __name__ == '__main__':
    unittest.main()
