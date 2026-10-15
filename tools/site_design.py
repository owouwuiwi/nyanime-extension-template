"""The demo's presentation layer; extraction contracts remain unchanged."""
import html
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'website'
ARROW = '<span aria-hidden="true">↗</span>'


def shell(title, body):
    template = (ROOT / 'web/shell.html').read_text(encoding='utf-8')
    return template.replace('{{title}}', html.escape(title)).replace('{{body}}', body)


def write(relative, text):
    path = SITE / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    family = relative.split('/')[0]
    match = re.search(r'demo-(\d+)', relative)
    number = (int(match[1]) - 1) % 3 + 1 if match else 1
    if family in {'video', 'manga', 'news', 'tv'} and 'chapter-' not in relative:
        art = '/example/art/' + (family + '-' + str(number) + '.svg' if family != 'tv' else 'tv.svg')
        text = re.sub(r'(<img\b[^>]*src=")/example/images/[^"/]+\.png("[^>]*>)', lambda m: m[1] + art + m[2], text)
        text = re.sub(r'poster="/example/images/[^"]+"', 'poster="' + art + '"', text)
    path.write_text(text, encoding='utf-8')


def data_script(value):
    return '<script id="entry-data" type="application/json">' + json.dumps(value).replace('<', '\\u003c') + '</script>'


def breadcrumb(label, url='/example/'):
    return '<nav class="breadcrumbs" aria-label="Breadcrumb"><a href="/example/">Playground</a><span aria-hidden="true">/</span><a href="' + url + '">' + html.escape(label) + '</a></nav>'


def card(url, title, image, label, kind, description):
    match = re.search(r'demo-(\d+)', url)
    index = int(match[1]) if match else 1
    art = 'tv.svg' if kind == 'tv' else kind + '-' + str((index - 1) % 3 + 1) + '.svg'
    title = title.replace('DEMO ', '').replace('article', 'Article')
    details = {'video': '3 episodes · Qualities & subtitles', 'manga': '3 chapters · Ordered pages', 'news': 'Native article · Text & images', 'tv': 'Finite signal · No live guide'}
    return ('<a class="demo-card glass" data-kind="' + kind + '" href="/example/' + url + '">'
            '<div class="demo-art"><img src="/example/art/' + art + '" width="960" height="640" alt="" loading="lazy" decoding="async"><span class="demo-open" aria-hidden="true">↗</span></div>'
            '<div class="demo-copy"><p class="demo-type">' + ('TV' if kind == 'tv' else kind.title()) + '<span>DEMO ' + f'{index:02}' + '</span></p>'
            '<h3>' + html.escape(title) + '</h3><p>' + details[kind] + '</p></div></a>')


def enhance(entries, articles):
    for name in ['style.css', 'playground.js']:
        shutil.copyfile(ROOT / 'web' / name, SITE / name)
    brand = ROOT / 'web/brand'
    if brand.is_dir():
        shutil.copytree(brand, SITE / 'brand', dirs_exist_ok=True)

    shutil.copytree(ROOT / 'web/art', SITE / 'art', dirs_exist_ok=True)
    grouped = {'video': [], 'manga': [], 'news': [], 'tv': []}
    for entry in entries:
        kind = 'video' if entry['medium'] == 'anime' else 'manga'
        grouped[kind].append(card(entry['url'], entry['title'], entry['cover'], '', kind, ''))
    grouped['news'] = [card(a['url'], a['title'], a['image'], '', 'news', '') for a in articles]
    grouped['tv'] = [card('tv/test-signal/', 'The quiet channel.', '', '', 'tv', '')]
    cards = ''.join(grouped[kind][i] for i in range(max(map(len, grouped.values()))) for kind in grouped if i < len(grouped[kind]))
    body = (ROOT / 'web/playground.html').read_text(encoding='utf-8').replace('{{demo_cards}}', cards)
    write('index.html', shell('Extension playground', body))

    for entry in entries:
        path = SITE / entry['url'] / 'index.html'
        original = path.read_text(encoding='utf-8')
        data = json.loads(re.search(r'<script id="entry-data" type="application/json">(.*?)</script>', original).group(1))
        ordered = sorted(data['parts'], key=lambda part: part['number'])
        medium = 'Episode' if entry['medium'] == 'anime' else 'Chapter'
        rows = ''.join('<a class="part-row glass" data-reveal href="/example/' + part['url'] + '"><span class="part-number">' + f'{int(part["number"]):02d}' + '</span><div><strong>' + html.escape(part['name']) + '</strong><small>' + ('Silent original clip · 12 seconds' if entry['medium']=='anime' else 'Original geometric story · '+str(5 if part['number']==2 else 6)+' pages') + '</small></div><span class="part-action" aria-hidden="true">' + ('▶' if entry['medium']=='anime' else '↗') + '</span></a>' for part in ordered)
        body = '<main id="main" class="detail-page">' + breadcrumb('Original demos') + '<section class="title-hero"><div class="detail-cover" data-reveal><img src="/example/' + entry['cover'] + '" width="600" height="900" alt="Cover of '+html.escape(entry['title'],quote=True)+'"></div><div class="title-copy"><p class="eyebrow" data-reveal>ORIGINAL DEMO · '+('WATCH' if entry['medium']=='anime' else 'READ')+'</p><h1 data-reveal>'+html.escape(entry['title'])+'</h1><div class="title-tags" data-reveal><span>'+entry['genre']+'</span><span>Completed</span><span>3 '+medium.lower()+'s</span></div><p class="title-description" data-reveal>'+html.escape(entry['description'])+'</p><a href="/example/'+ordered[0]['url']+'" class="button primary" data-reveal>'+('Start watching' if entry['medium']=='anime' else 'Start reading')+' <span aria-hidden="true">'+('▶' if entry['medium']=='anime' else '↗')+'</span></a></div></section><section class="parts-section"><div class="section-heading demo-heading" data-reveal><h2>'+medium+'s</h2><p>Start at the beginning. Pick up wherever you like.</p></div><div class="part-list">'+rows+'</div></section><aside class="developer-note glass" data-reveal><span class="feature-icon" aria-hidden="true">⌘</span><div><strong>A real page, a simple contract.</strong><p>The extension extracts this title and its '+medium.lower()+'s from the page’s structured data. The host stays source-agnostic.</p><a class="text-link" href="/example/guide/">See how it works '+ARROW+'</a></div></aside></main>'+data_script(data)
        write(entry['url']+'index.html',shell(entry['title'],body))
        for index, part in enumerate(ordered):
            previous = ordered[index-1] if index else None
            following = ordered[index+1] if index+1 < len(ordered) else None
            navigation = '<nav class="part-navigation" aria-label="'+medium+' navigation">'+('<a class="text-link" href="/example/'+previous['url']+'">← Previous '+medium.lower()+'</a>' if previous else '<span></span>')+'<a href="/example/'+entry['url']+'">All '+medium.lower()+'s</a>'+('<a class="text-link" href="/example/'+following['url']+'">Next '+medium.lower()+' →</a>' if following else '<span class="end-label">You’re all caught up.</span>')+'</nav>'
            heading = breadcrumb(entry['title'],'/example/'+entry['url'])+'<div class="playback-heading" data-reveal><div><p class="eyebrow">'+('ORIGINAL DEMO CLIP' if entry['medium']=='anime' else 'ORIGINAL DEMO MANGA')+'</p><h1>'+medium+' '+f'{int(part["number"]):02d}'+'</h1><p>'+html.escape(entry['title'])+'</p></div><a class="text-link" href="/example/'+entry['url']+'">Back to the story '+ARROW+'</a></div>'
            if entry['medium']=='anime':
                old = (SITE/part['url']/'index.html').read_text(encoding='utf-8')
                sources = re.search(r'<video[^>]*>(.*?)</video>',old).group(1)
                body='<main id="main" class="playback-page">'+heading+'<div class="cinema-frame" data-reveal><video controls preload="metadata" playsinline poster="/example/'+entry['banner']+'" aria-label="'+html.escape(part['name'],quote=True)+'">'+sources+'</video></div><div class="playback-details"><div><span class="status-chip">ORIGINAL · 12 SECONDS</span><h2>A quiet little test.</h2><p>This is an intentionally black, silent test clip. Try playback, seeking, quality selection and English subtitles.</p></div><div class="quality-control" role="group" aria-label="Video quality"><span>Playback quality</span><div class="quality-options"><button type="button" data-quality="360" aria-pressed="true">360p</button><button type="button" data-quality="180" aria-pressed="false">180p</button></div></div></div>'+navigation+'<aside class="developer-note glass" data-reveal><span class="feature-icon" aria-hidden="true">⌘</span><div><strong>Two qualities. One page.</strong><p>The adapter reads the video’s source and subtitle tags. No player or website logic is added to Nyanime.</p><a class="text-link" href="/example/guide/#video-adapter">Explore the video adapter '+ARROW+'</a></div></aside></main>'
            else:
                images=''.join('<img data-page="'+str(n)+'" src="/example/images/pages/'+f'{n:02d}'+'.png" width="800" height="1120" alt="Original demo manga page '+str(n)+'" loading="'+('eager' if n==1 else 'lazy')+'" decoding="async">' for n in range(1,6 if part['number']==2 else 7))
                body='<div class="reader-heading">'+heading+'</div><div class="reader-info"><span class="status-chip">ORIGINAL ARTWORK</span><p>A circle. A triangle. A small adventure.</p></div><main class="reader" id="main" aria-label="Manga pages">'+images+'</main>'+navigation
            write(part['url']+'index.html',shell(part['name'],body))

    for article in articles:
        body='<main id="main" class="article-page">'+breadcrumb('Original news demos')+'<p class="eyebrow" data-reveal>THE PLAYGROUND JOURNAL</p><h1 data-reveal>'+html.escape(article['title'])+'</h1><p class="article-excerpt" data-reveal>'+html.escape(article['excerpt'])+'</p><div class="article-byline">Placeholder Studio <span>·</span> Original sample text <span>·</span> CC0-1.0</div><img class="article-image" src="/example/'+article['image']+'" width="960" height="540" alt="Original geometric illustration" data-reveal><div class="article-body"><h2>Small beginnings. Clear possibilities.</h2><p>'+html.escape(article['body'])+'</p><p>The same source can publish articles about watching and reading. This sample demonstrates pagination, native text blocks and media categories with verifiable publication metadata.</p></div><a class="text-link" href="/example/#demos">Explore more demos '+ARROW+'</a></main>'+data_script(article)
        write(article['url']+'index.html',shell(article['title'],body))
    write('tv/test-signal/index.html',shell('The quiet channel','<main id="main" class="playback-page">'+breadcrumb('TV demo')+'<div class="playback-heading" data-reveal><div><p class="eyebrow">SYNTHETIC TV FIXTURE</p><h1>The quiet channel.</h1><p>An original, finite signal for testing the TV adapter.</p></div></div><div class="cinema-frame" data-reveal><video controls preload="metadata" playsinline poster="/example/images/video-03-wide.png" aria-label="Finite synthetic TV test"><source src="/example/media/tv-test.mp4" type="video/mp4"></video></div><div class="playback-details"><div><span class="status-chip">FINITE DEMO · 2 HOURS</span><h2>No invented programme guide.</h2><p>This is an intentionally black test file, not a live broadcaster. The extension declares guide, rewind and shared live clock as unavailable.</p></div><a class="text-link" href="/example/guide/#tv-adapter">Explore the TV contract '+ARROW+'</a></div></main>'))
