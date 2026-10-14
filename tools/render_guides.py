#!/usr/bin/env python3
"""Render the same English Markdown guides as responsive static pages."""
import html
import re
import shutil
from pathlib import Path
import markdown
from site_design import shell

ROOT = Path(__file__).resolve().parents[1]


def render():
    target = ROOT / 'website'
    pages = [('README.md', 'guide/index.html', 'Quick start'),
             ('docs/REFERENCE.md', 'reference/index.html', 'Technical reference'),
             ('docs/CHECKLIST.md', 'checklist/index.html', 'Release checklist')]
    routes = {'docs/REFERENCE.md': '/example/reference/', 'docs/CHECKLIST.md': '/example/checklist/',
              '../README.md': '/example/guide/', '../README.md#': '/example/guide/#',
              'REFERENCE.md': '/example/reference/', 'CHECKLIST.md': '/example/checklist/',
              'website/ASSETS.md': '/example/ASSETS.md'}
    for source, destination, title in pages:
        text = (ROOT / source).read_text(encoding='utf-8')
        for old, new in routes.items():
            text = text.replace('](' + old + ')', '](' + new + ')').replace('](' + old + '#', '](' + new + '#')
        renderer = markdown.Markdown(extensions=['fenced_code', 'tables', 'toc'])
        body = renderer.convert(text)
        sidebar = '<aside class="doc-sidebar" aria-label="Documentation navigation"><p>DEVELOPER HANDBOOK</p><a href="/example/guide/">01 · Quick start</a><a href="/example/reference/">02 · Technical reference</a><a href="/example/checklist/">03 · Release checklist</a><details class="doc-toc"><summary>On this page</summary>' + renderer.toc + '</details></aside>'
        document = shell(title, '<main id="main" class="docs-layout"><article class="docs-article">' + body + '</article>' + sidebar + '</main>')
        file = target / destination
        file.parent.mkdir(exist_ok=True)
        file.write_text(document, encoding='utf-8')
    shutil.copyfile(ROOT / 'README.md', target / 'README.md')
    index = target / 'index.html'
    text = index.read_text(encoding='utf-8').replace('href="README.md"', 'href="guide/"')

    index.write_text(text, encoding='utf-8')
    print('Rendered quick start, technical reference and release checklist.')


if __name__ == '__main__':
    render()
