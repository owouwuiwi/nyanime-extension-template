#!/usr/bin/env python3
"""Render one canonical developer guide; preserve the old documentation URLs."""
import html
import hashlib
import shutil
from pathlib import Path
from urllib.parse import urlsplit

import markdown
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor
from site_design import shell

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = 'https://github.com/owouwuiwi/nyanime-extension-template/blob/main/'


def web_link(source, href):
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc or href.startswith(('/', '#')):
        return href
    path = (ROOT / source).parent.joinpath(parsed.path).resolve()
    relative = path.relative_to(ROOT).as_posix()
    if not path.is_file():
        raise ValueError('Documentation target does not exist: ' + relative)
    fragment = '#' + parsed.fragment if parsed.fragment else ''
    if relative in {'docs/GUIDE.md', 'docs/REFERENCE.md'}:
        return '/example/guide/' + fragment
    if relative == 'docs/INTEROPERABILITY.md':
        return '/example/guide/#for-existing-extension-authors'
    if relative == 'docs/CHECKLIST.md':
        return '/example/guide/#release-checklist'
    if relative == 'website/ASSETS.md':
        return '/example/ASSETS.md' + fragment
    return REPOSITORY + relative + fragment


class WebLinks(Extension):
    def __init__(self, source):
        self.source = source
        super().__init__()

    def extendMarkdown(self, md):
        source = self.source

        class Links(Treeprocessor):
            def run(self, root):
                for link in root.iter('a'):
                    link.set('href', web_link(source, link.get('href', '')))

        md.treeprocessors.register(Links(md), 'public-source-links', 2)


def redirect(checklist=False):
    target = '/example/guide/' + ('#release-checklist' if checklist else '')
    # The old reference's section anchors still exist in the unified guide.
    script_target = "'/example/guide/#release-checklist'" if checklist else "'/example/guide/' + location.hash"
    return ('<!doctype html><html lang="en"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Developer guide · Nyanime</title>'
            '<link rel="canonical" href="https://owouwuiwi.github.io' + target + '">'
            '<meta http-equiv="refresh" content="0;url=' + target + '">'
            '<script>location.replace(' + script_target + ')</script>'
            '<p>The documentation is now in one place. <a href="' + html.escape(target) + '">'
            'Open the complete developer guide</a>.</p></html>')


def render():
    target = ROOT / 'website'
    source = 'docs/GUIDE.md'
    renderer = markdown.Markdown(
        extensions=['fenced_code', 'tables', 'toc', WebLinks(source)],
        extension_configs={'toc': {'toc_depth': '2-2'}},
    )
    original = (ROOT / source).read_text(encoding='utf-8')
    body = renderer.convert(original)
    legacy = {
        '1-get-ready': 'set-up-and-build-the-unchanged-example',
        '2-configure': 'configure-identity-and-discovery',
        '3-build-and-test': 'signing-and-updates',
        '4-make-your-rin': 'signing-and-updates',
        '5-open-in-nyanime': 'install-and-check-the-result',
        'make-it-yours': 'home-categories-sections-and-filters',
    }
    for old, current in legacy.items():
        marker = 'id="' + current + '">'
        body = body.replace(marker, marker + '<span id="' + old + '" class="doc-anchor" aria-hidden="true"></span>', 1)
    sidebar = ('<aside class="doc-sidebar" aria-label="Documentation navigation">'
               '<p>THE DEVELOPER GUIDE</p><a href="/example/">← Back to the playground</a>'
               '<nav class="doc-index" aria-label="In this guide">' + renderer.toc + '</nav>'
               '<details class="doc-toc"><summary>In this guide</summary>' + renderer.toc + '</details>'
               '<a href="' + REPOSITORY + source + '">Read on GitHub ↗</a></aside>')
    document = shell('Developer guide', '<main id="main" class="docs-layout">'
                     '<article class="docs-article" data-source-sha256="' + hashlib.sha256(original.encode('utf-8')).hexdigest() + '">'
                     + body + '</article>' + sidebar + '</main>')
    guide = target / 'guide/index.html'
    guide.parent.mkdir(parents=True, exist_ok=True)
    guide.write_text(document, encoding='utf-8')
    for name in ['reference', 'checklist']:
        old = target / name / 'index.html'
        old.parent.mkdir(parents=True, exist_ok=True)
        old.write_text(redirect(checklist=name == 'checklist'), encoding='utf-8')
    shutil.copyfile(ROOT / 'README.md', target / 'README.md')
    print('Rendered one complete developer guide; old reference/checklist URLs redirect to it.')


if __name__ == '__main__':
    render()
