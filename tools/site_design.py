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
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#130f16">
<meta name="description" content="The Nyanime extension playground. Original demo content and one complete guide to Nyanime extension APIs, Home categories, building, signing and testing.">
<meta name="robots" content="noindex"><link rel="icon" href="/example/brand/mark.svg" type="image/svg+xml">
<script>try{const t=localStorage.getItem('nyanime-theme');document.documentElement.dataset.theme=t==='light'||t==='dark'?t:matchMedia('(prefers-color-scheme:light)').matches?'light':'dark'}catch{}</script>
<link rel="stylesheet" href="/example/brand/nyanime.css?v=2"><link rel="stylesheet" href="/example/style.css?v=3">
<script src="/example/playground.js?v=2" defer></script><title>''' + html.escape(title) + ''' · Nyanime</title></head><body>
<a class="skip" href="#main">Skip to content</a><div class="site-shell">
<header class="header glass"><a href="/" class="brand" aria-label="Nyanime home"><img class="logo dark-logo" src="/example/brand/logo-dark.svg" width="164" height="47" alt="Nyanime"><img class="logo light-logo" src="/example/brand/logo-light.svg" width="164" height="47" alt="Nyanime"></a><a class="playground-label" href="/example/">Playground <span>FOR CREATORS</span></a><nav aria-label="Playground navigation"><a class="desktop-nav" href="/example/#demos">Demos</a><a class="nav-download" href="/example/guide/">Start building <span aria-hidden="true">↗</span></a><button class="theme-button" aria-label="Switch to light theme"><svg class="theme-icon theme-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/></svg><svg class="theme-icon theme-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M20.5 14.4A8.6 8.6 0 0 1 9.6 3.5a8.6 8.6 0 1 0 10.9 10.9Z"/></svg></button></nav></header>
''' + body + '''
<footer class="footer playground-footer"><div class="footer-main"><a href="/example/" class="footer-wordmark">Made to be <span class="accent-text">made yours.</span></a><nav aria-label="Developer links"><a href="/example/guide/">Developer guide</a><a href="/example/guide/#choosing-a-family">API overview</a><a href="/example/guide/#release-checklist">Release checklist</a><a href="/example/ASSETS.md">Media credits</a></nav></div><p class="copyright-position"><strong>Nyanime does not promote piracy in any way or form.</strong><br>Bring your own content. Respect creators and copyright. <a href="https://owouwuiwi.github.io/responsible-use/">Our position ↗</a></p><p>© 2026 owouwuiwi &amp; Nyanime contributors. Original demo media: CC0-1.0.<br>Extension code: Apache-2.0. Font licences are included with the starter.</p></footer></div></body></html>'''


def write(relative, text):
    path = SITE / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def data_script(value):
    return '<script id="entry-data" type="application/json">' + json.dumps(value).replace('<', '\\u003c') + '</script>'


def breadcrumb(label, url='/example/'):
    return '<nav class="breadcrumbs" aria-label="Breadcrumb"><a href="/example/">Playground</a><span aria-hidden="true">/</span><a href="' + url + '">' + html.escape(label) + '</a></nav>'


def card(url, title, image, label, kind, description):
    return '<a class="demo-card glass" data-kind="' + kind + '" data-reveal href="/example/' + url + '"><div class="demo-art"><img src="/example/' + image + '" width="600" height="900" alt="" loading="lazy" decoding="async"><span class="demo-type">' + label + '</span><span class="demo-open" aria-hidden="true">↗</span></div><div class="demo-copy"><h3>' + html.escape(title) + '</h3><p>' + html.escape(description) + '</p></div></a>'


def enhance(entries, articles):
    for name in ['style.css', 'playground.js']:
        shutil.copyfile(ROOT / 'web' / name, SITE / name)
    brand = ROOT / 'web/brand'
    if brand.is_dir():
        shutil.copytree(brand, SITE / 'brand', dirs_exist_ok=True)

    cards = ''.join(card(e['url'], e['title'], e['cover'], 'WATCH' if e['medium'] == 'anime' else 'READ',
                         'video' if e['medium'] == 'anime' else 'manga', e['genre'] + ' · 3 original ' + ('episodes' if e['medium'] == 'anime' else 'chapters')) for e in entries)
    cards += ''.join(card(a['url'], a['title'], a['image'], 'NEWS', 'news', 'Original article · Native reading blocks') for a in articles)
    cards += card('tv/test-signal/', 'The quiet channel.', 'images/video-03-wide.png', 'TV DEMO', 'tv', 'Finite synthetic signal · No live guide')
    hero = '''<section class="playground-hero"><div class="playground-hero-copy"><p class="eyebrow" data-reveal><span class="status-dot" aria-hidden="true"></span> THE EXTENSION PLAYGROUND</p><h1 data-reveal>Your next extension.<br><span class="accent-text">Starts here.</span></h1><p class="hero-description" data-reveal>A little world to build with.<br>Real pages. Original stories. Your own possibilities.</p><div class="hero-actions" data-reveal><a class="button primary" href="guide/">Read the developer guide <span aria-hidden="true">↗</span></a><a class="text-link" href="#demos">Explore the demos <span aria-hidden="true">↓</span></a></div><p class="micro" data-reveal>Open source · No sign-in · Original demo media</p></div><div class="playground-stage" aria-hidden="true"><div class="stage-orbit"></div><div class="stage-spark spark-one">✦</div><div class="stage-spark spark-two">✦</div><div class="stage-book book-back"><img src="images/manga-02.png" alt="" width="600" height="900"></div><div class="stage-book book-front"><img src="images/video-01.png" alt="" width="600" height="900"></div><div class="stage-caption glass"><span class="stage-caption-icon">✦</span><div><small>ONE EXTENSION.</small><strong>A whole new Home.</strong></div><span aria-hidden="true">↗</span></div></div></section>'''
    filters = '<div class="demo-filters t-tabs" role="group" aria-label="Filter demo types"><span class="t-tabs-pill" aria-hidden="true"></span>' + ''.join('<button class="t-tab" type="button" data-filter="'+key+'" aria-pressed="'+('true' if key=='all' else 'false')+'">'+label+'</button>' for key,label in [('all','All'),('video','Video'),('manga','Manga'),('news','News'),('tv','TV')]) + '</div>'
    body = '<main id="main">' + hero + '''<div class="intro-strip playground-strip"><div data-reveal><span class="strip-icon" aria-hidden="true">◈</span><p>One starting point.<small>Video, manga, news and TV.</small></p></div><div data-reveal><span class="strip-icon" aria-hidden="true">✦</span><p>Entirely original.<small>No third-party stories or streams.</small></p></div><div data-reveal><span class="strip-icon" aria-hidden="true">↗</span><p>Ready to make yours.<small>Source, tools and clear documentation.</small></p></div></div><section class="section" id="demos"><div class="section-heading demo-heading" data-reveal><div><p class="eyebrow">A SMALL WORLD. REAL POSSIBILITIES.</p><h2>Take it for a spin.</h2></div><p>Open a story, play a clip, turn a page.<br>These are the pages the extensions actually read.</p></div>''' + filters + '<p class="demo-count" role="status" aria-live="polite">22 demos to explore</p><div class="demo-grid">' + cards + '</div></section>' + '''<section class="section developer-paths" aria-labelledby="paths-title"><div class="section-heading" data-reveal><p class="eyebrow">ONE GUIDE. EVERYTHING CONNECTED.</p><h2 id="paths-title">From first build.<br>To your own extension.</h2></div><a href="guide/" class="path-card glass guide-path" data-reveal><span class="path-number" aria-hidden="true">⌘</span><div><p class="eyebrow">THE COMPLETE DEVELOPER GUIDE</p><h3>Understand it. Build it. Make it yours.</h3><p>Public APIs explained with real code, website parsing, dynamic Home categories, signing, installation and testing. One guide, with an index to find what you need.</p><span class="text-link">Open the guide <span aria-hidden="true">↗</span></span></div></a></section><section class="section"><div class="starter-panel glass" data-reveal><div><p class="eyebrow">MAKE SOMETHING OF YOUR OWN</p><h2>Take the starter.<br><span class="accent-text">Make it yours.</span></h2><p>Four examples, a matching SDK, original fixtures and tests.</p></div><a href="downloads/placeholder-extension-kit.zip" class="button primary">Download the kit <span aria-hidden="true">↓</span></a></div></section></main>'''
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
