#!/usr/bin/env python3
"""Create original geometric artwork and a tiny static source website. No downloads."""
import argparse
import hashlib
import html
import json
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'website'
PUBLISHED_AT = 1791936000000  # Fixed publication metadata, never the fetch time.


def write(name, text):
    target = SITE / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding='utf-8', newline='\n')


def page(title, body, data=None):
    payload = '' if data is None else '<script id="entry-data" type="application/json">' + json.dumps(data).replace('<', '\\u003c') + '</script>'
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' + \
        '<meta name="robots" content="noindex"><title>' + html.escape(title) + '</title><link rel="stylesheet" href="/example/style.css">' + \
        '<header><a href="/example/">◇ PLACEHOLDER STUDIO</a><span>Original demo content · No third-party catalogue</span></header>' + \
        body + payload + '<footer>Original demonstration assets · CC0-1.0. <a href="/example/ASSETS.md">Provenance & licence</a> · <a href="/example/api/catalogue.json">Public JSON</a></footer></html>'


def picture(path, number=1, landscape=False):
    width, height = (960, 540) if landscape else (600, 900)
    palette = [(252, 181, 75), (82, 190, 226), (178, 160, 242)]
    accent = palette[(number - 1) % len(palette)]
    image = Image.new('RGB', (width, height), (20, 24, 35))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((24, 24, width - 24, height - 24), 30, outline=accent, width=4)
    draw.ellipse((width//4, height//4, width*3//4, height*3//4), fill=accent)
    draw.polygon([(width//2, height//3), (width//3, height*2//3), (width*2//3, height*2//3)], fill=(20,24,35))
    draw.text((50, 55), 'ORIGINAL DEMO / %02d' % number, fill='white', font=ImageFont.load_default(size=24))
    draw.text((50, height-80), 'PLACEHOLDER STUDIO', fill='white', font=ImageFont.load_default(size=22))
    target = SITE / path
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, optimize=True)


def manga_page(number):
    image = Image.new('RGB', (800, 1120), 'white')
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=23)
    draw.text((40,25), f'DEMO MANGA / ORIGINAL PAGE {number:02d}', font=font, fill='black')
    captions = ['A circle leaves home.', 'A triangle joins the trip.', 'The road bends.',
                'A square has an idea.', 'They cross the bridge.', 'A new chapter begins.']
    for panel in range(3):
        top = 85 + panel*326
        draw.rectangle((30, top, 770, top+304), outline='black', width=4)
        draw.line((32, top+225, 768, top+225), fill='black', width=3)
        shift = (number*35 + panel*70) % 250
        draw.ellipse((95+shift,top+105,195+shift,top+205), outline='black', width=4)
        draw.ellipse((121+shift,top+135,129+shift,top+143), fill='black')
        draw.ellipse((161+shift,top+135,169+shift,top+143), fill='black')
        draw.arc((120+shift,top+145,170+shift,top+180), 10, 170, fill='black', width=3)
        draw.polygon([(490,top+105),(550,top+205),(430,top+205)], outline='black', width=4)
        draw.rounded_rectangle((55,top+24,710,top+76), radius=18, outline='black', width=2)
        draw.text((76,top+40), captions[(number+panel-1)%len(captions)], font=font, fill='black')
    draw.text((360,1073), str(number), font=font, fill='black')
    target = SITE / f'images/pages/{number:02d}.png'
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, optimize=True)


def build(ffmpeg=None):
    SITE.mkdir(parents=True, exist_ok=True)
    write('style.css', 'body{margin:0;background:#11151f;color:#f4f2ed;font:17px/1.6 system-ui,sans-serif}header,main,footer{max-width:1040px;margin:auto;padding:24px}header{display:flex;flex-wrap:wrap;gap:18px;justify-content:space-between;border-bottom:1px solid #334}header span,footer{font-size:14px;color:#aeb5c5}a{color:#ffc565}h1{font-size:clamp(30px,6vw,56px);line-height:1.1}p{max-width:720px}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:20px}.cards a{padding:12px;border-radius:18px;background:#202637;text-decoration:none}.cards img{width:100%;aspect-ratio:2/3;object-fit:cover;border-radius:12px}.reader{max-width:800px;padding:0}.reader img{display:block;width:100%;height:auto;margin:0}.badge{display:inline-block;padding:5px 12px;border:1px solid #6c7285;border-radius:99px}video{display:block;max-width:100%;width:900px;background:#000}li{margin:12px 0}code{word-break:break-word}.guide{padding:20px;border:1px solid #334;border-radius:18px}')
    entries = []
    for medium, total in [('anime', 9), ('manga', 6)]:
        for number in range(1,total+1):
            kind = 'video' if medium == 'anime' else 'manga'
            stem = f'{kind}/demo-{number:02d}'
            cover = f'images/{kind}-{number:02d}.png'
            banner = f'images/{kind}-{number:02d}-wide.png'
            picture(cover, number)
            picture(banner, number, True)
            entry = {'id':f'{kind}-{number:02d}','medium':medium,'title':f'DEMO {kind.title()} {number:02d}',
                'url':stem+'/','cover':cover,'banner':banner,'genre':['Adventure','Slice of life','Fantasy'][(number-1)%3],
                'format':'Cartoons' if medium=='anime' and number>6 else 'Animation' if medium=='anime' else 'Manga',
                'description':'An original synthetic example for extension authors. No real series, characters, catalogue IDs or publication claims.',
                'publishedAt':PUBLISHED_AT+(number-1)*60_000}
            parts=[]
            for part in range(1,4):
                reference=f'{stem}/{"episode" if medium=="anime" else "chapter"}-{part:02d}/'
                parts.append({'url':reference, 'name':f'DEMO {"Episode" if medium=="anime" else "Chapter"} {part}',
                              'number':part,'publishedAt':PUBLISHED_AT+(part-1)*60_000})
                if medium == 'anime':
                    body='<main><span class="badge">ORIGINAL SYNTHETIC VIDEO</span><h1>DEMO Episode '+str(part)+'</h1><p>A silent black test clip. This is intentional, not a broken stream.</p><video controls preload="metadata"><source src="/example/media/demo-360.mp4" type="video/mp4" data-label="360p demo" data-height="360"><source src="/example/media/demo-180.mp4" type="video/mp4" data-label="180p demo" data-height="180"><track kind="subtitles" src="/example/media/demo-en.vtt" srclang="en" label="English" default></video></main>'
                else:
                    pages=range(1,7) if part!=2 else range(1,6)  # Deliberately odd chapter for spread tests.
                    body='<main class="reader">'+''.join(f'<img data-page="{n}" src="/example/images/pages/{n:02d}.png" alt="Original geometric demo page {n}" loading="lazy">' for n in pages)+'</main>'
                write(reference+'index.html',page(parts[-1]['name'],body))
            data={'entry':entry,'parts':parts}
            links=''.join(f'<li><a class="episode-link" href="/example/{part["url"]}">{part["name"]}</a></li>' for part in parts)
            write(stem+'/index.html',page(entry['title'],'<main><span class="badge">DEMO / NO REAL CATALOGUE IDS</span><h1>'+entry['title']+'</h1><p>'+entry['description']+'</p><ul>'+links+'</ul></main>',data))
            entries.append(entry)
    for number in range(1,7): manga_page(number)
    picture('images/logo.png', 1, True)
    icon = Image.new('RGB', (256, 256), (25, 35, 51))
    pen = ImageDraw.Draw(icon)
    pen.rounded_rectangle((8, 8, 248, 248), radius=48, outline=(119, 204, 238), width=6)
    pen.polygon([(128, 36), (220, 128), (128, 220), (36, 128)], fill=(119, 204, 238))
    pen.polygon([(110, 87), (168, 128), (110, 169)], fill=(25, 35, 51))
    icon.save(SITE / 'images/icon.png', optimize=True)
    write('api/catalogue.json',json.dumps({'schema':1,'entries':entries},ensure_ascii=False,indent=2)+'\n')
    articles=[]
    for number in range(1,7):
        article={'id':f'article-{number:02d}', 'url':f'news/demo-{number:02d}/', 'title':f'DEMO article {number:02d}',
            'publishedAt':PUBLISHED_AT+number*60_000,'excerpt':'An original sample article demonstrating a native news reader.',
            'image':f'images/video-{number:02d}-wide.png','medium':'ANIME' if number%2 else 'MANGA',
            'category':'development','body':'This article is original demonstration text. It shows headings, paragraphs, images and exact publication metadata. There are no real catalogue IDs, external publishers, advertisements or tracking scripts.'}
        articles.append(article)
        write(article['url']+'index.html',page(article['title'],'<main><h1>'+article['title']+'</h1><p>'+article['body']+'</p></main>',article))
    write('api/news.json',json.dumps({'schema':1,'articles':articles},indent=2)+'\n')
    write('api/tv.json',json.dumps({'schema':1,'channels':[{'id':'test-signal','name':'DEMO — synthetic test signal',
        'logo':'images/icon.png','stream':'media/tv-test.mp4','description':'A finite two-hour synthetic file, not a real live broadcast. No UTC synchronization or DVR is claimed.'}]},indent=2)+'\n')
    cards=''.join(f'<a href="/example/{entry["url"]}"><img src="/example/{entry["cover"]}" alt=""><strong>{entry["title"]}</strong><br>{entry["genre"]}</a>' for entry in entries)
    write('index.html',page('Placeholder Studio — Nyanime extension demo','<main><span class="badge">DEVELOPER DEMO</span><h1>A source you can<br>understand.</h1><p>Everything here is original demonstration material: geometric illustrations, silent synthetic video and sample articles. The extension extracts these pages through the same public contracts as any other source.</p><p><a href="downloads/placeholder-extension-kit.zip">Download the developer kit</a> · <a href="README.md">Five-step guide</a></p><div class="cards">'+cards+'</div></main>'))
    write('media/demo-en.vtt','WEBVTT\n\n00:00:00.000 --> 00:00:05.000\nOriginal silent DEMO clip. A black image is intentional.\n\n00:00:05.000 --> 00:00:12.000\nPlayback, seeking and subtitle selection can be tested here.\n')
    if ffmpeg:
        for name, size, duration in [('demo-360.mp4','640x360',12),('demo-180.mp4','320x180',12),('tv-test.mp4','320x180',7200)]:
            output=SITE/'media'/name
            if output.exists(): continue
            subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-f','lavfi','-i',f'color=c=black:s={size}:r=2',
                '-f','lavfi','-i','anullsrc=channel_layout=stereo:sample_rate=48000','-t',str(duration),
                '-c:v','libx264','-preset','ultrafast','-crf','35','-pix_fmt','yuv420p','-c:a','aac','-b:a','8k',
                '-movflags','+faststart','-y',str(output)],check=True)
    from site_design import enhance
    enhance(entries, articles)
    assets={p.relative_to(SITE).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(SITE.rglob('*')) if p.is_file() and p.suffix in {'.png','.mp4','.vtt'}}
    write('assets-manifest.json',json.dumps({'license':'CC0-1.0','origin':'Generated locally from geometric primitives and synthetic black video; no third-party media.',
        'generator':'tools/generate_site.py','assets':assets},indent=2)+'\n')
    write('ASSETS.md','# Original demo assets\n\nAll demo illustrations, sample story text, subtitles and video were created specifically for this example. No scans, anime clips, characters, music or third-party publisher data are used.\n\nNyanime branding and the bundled font files are excluded from this dedication. Branding retains its existing copyright; fonts retain the licences included in brand/. No trademark rights are granted.\n\nThe generated demo media and sample text are dedicated to the public domain under CC0-1.0: https://creativecommons.org/publicdomain/zero/1.0/\n\nThe generator and extension code use Apache-2.0. FFmpeg is a local generation tool; its binary is not distributed in this kit or website. The hashes of generated media are in assets-manifest.json. The TV test file is finite; it is not advertised as a real live broadcast.\n')
    print(f'Generated {len(entries)} titles, six original manga pages, three chapters per title, six articles and a synthetic TV fixture.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffmpeg',help='Optional path to a local FFmpeg executable to generate synthetic MP4 files')
    args=parser.parse_args()
    build(args.ffmpeg)
