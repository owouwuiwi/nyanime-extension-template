#!/usr/bin/env python3
"""Validate the single configuration file and generate matching manifests/Home contracts."""
import json
import re
import shutil
from pathlib import Path
from urllib.parse import urlparse
from xml.sax.saxutils import escape

ROOT=Path(__file__).resolve().parents[1]

def configure(root=ROOT):
    config=json.loads((root/'template.json').read_text())
    base=urlparse(config['baseUrl'])
    if base.scheme!='https' or not base.hostname or base.username or base.password or base.query or base.fragment or not base.path.endswith('/'):
        raise ValueError('baseUrl must be an HTTPS website directory ending in /, without credentials or query parameters.')
    if not re.fullmatch(r'[a-z]{2}',config['language']): raise ValueError('Use a two-letter source language code.')
    if type(config['versionCode']) is not int or config['versionCode']<1: raise ValueError('versionCode must be a positive integer.')
    if not isinstance(config.get('versionName'), str) or not re.fullmatch(r'[0-9]+(?:\.[0-9]+){1,3}',config['versionName']):
        raise ValueError('versionName must be a dotted numeric version.')
    if type(config.get('minimumHostVersionCode')) is not int or config['minimumHostVersionCode'] < 232:
        raise ValueError('Standalone local import requires a compatible host (232+).')
    if set(config['modules']) != {'video','manga','news','tv','guide','addon'}:
        raise ValueError('Keep the six example module declarations, even when building only one.')
    ids=[]
    packages=[]
    for module in config['modules'].values():
        if not isinstance(module.get('name'),str) or not 1 <= len(module['name']) <= 100 or any(ord(c)<32 for c in module['name']):
            raise ValueError('Source name must be nonempty plain text, up to 100 characters.')
        if any(c in module['name'] for c in ['"', '\\', '$']):
            raise ValueError('Use a plain source name without build-script escape characters.')
        if not re.fullmatch(r'[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+',module['package']):
            raise ValueError('Invalid package name.')
        if type(module['sourceId']) is not int or not 0 < module['sourceId'] < 2**63:
            raise ValueError('sourceId must fit a positive signed 64-bit integer.')
        ids.append(module['sourceId'])
        packages.append(module['package'])
    if len(set(ids)) != len(ids) or len(set(packages)) != len(packages):
        raise ValueError('Each source needs a unique package and stable ID.')
    for kind,module in config['modules'].items():
        if kind not in {'video','manga','news','tv','guide','addon'}: raise ValueError('Unknown extension family.')
        if not re.fullmatch(r'[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+',module['package']): raise ValueError('Invalid package name.')
        if type(module['sourceId']) is not int or not 0<module['sourceId']<2**63: raise ValueError('sourceId must fit a positive signed 64-bit integer.')
        assets=root/kind/'src/main/assets'
        assets.mkdir(parents=True,exist_ok=True)
        package_label=escape(module['name'],{'"':'&quot;'})
        icon=root/kind/'src/main/res/drawable/extension_icon.xml'
        icon.parent.mkdir(parents=True,exist_ok=True)
        icon.write_text('<vector xmlns:android="http://schemas.android.com/apk/res/android" android:width="48dp" android:height="48dp" android:viewportWidth="48" android:viewportHeight="48"><path android:fillColor="#192333" android:pathData="M0,0h48v48h-48z"/><path android:fillColor="#77CCEE" android:pathData="M24,6L42,24L24,42L6,24z"/><path android:fillColor="#192333" android:pathData="M21,16L33,24L21,32z"/></vector>',encoding='utf-8')
        metadata=''
        if kind=='news':
            feature='nyanime.newsextension'
            metadata='<meta-data android:name="nyanime.news.api" android:value="1"/><meta-data android:name="nyanime.news.factory" android:value="example.placeholder.news.NewsFactory"/>'
        elif kind in {'guide', 'addon'}:
            feature = 'nyanime.guideextension' if kind == 'guide' else 'nyanime.addon'
            metadata = f'<meta-data android:name="nyanime.{kind}.api" android:value="1"/><meta-data android:name="nyanime.{kind}.factory" android:value="example.placeholder.{kind}.{kind.title()}Factory"/>'
        elif kind=='tv':
            feature='nyanime.tvextension'
            metadata='<meta-data android:name="nyanime.tv.api" android:value="1"/><meta-data android:name="nyanime.tv.factory" android:value="example.placeholder.tv.TvFactory"/>'
        else:
            feature='tachiyomi.animeextension' if kind=='video' else 'tachiyomi.extension'
            factory='example.placeholder.video.VideoFactory' if kind=='video' else 'example.placeholder.manga.MangaFactory'
            key='tachiyomi.animeextension.class' if kind=='video' else 'tachiyomi.extension.class'
            metadata=f'<meta-data android:name="{key}" android:value="{factory}"/><meta-data android:name="aniyomix.name" android:value="{package_label}"/><meta-data android:name="aniyomix.extensionLib" android:value="{int(module["api"]) if kind=="video" else module["api"]}"/>'
        manifest=f'<manifest xmlns:android="http://schemas.android.com/apk/res/android"><uses-feature android:name="{feature}" android:required="false"/><application android:label="{package_label}" android:icon="@drawable/extension_icon" android:allowBackup="false" android:supportsRtl="true">{metadata}</application></manifest>'
        (root/kind/'src/main/AndroidManifest.xml').write_text(manifest,encoding='utf-8')
        distribution=assets/'nyanime/extension-v1.json'
        distribution.parent.mkdir(parents=True,exist_ok=True)
        distribution.write_text(json.dumps({'version':1,'id':module['package'],'label':'Developer demo','updatePolicy':'manual'},indent=2)+'\n',encoding='utf-8')
        descriptor={'schema':1 if kind in {'video','manga'} else 2,
            'packageName':module['package'],'name':module['name'],'versionCode':config['versionCode'],
            'versionName':str(module['api'])+'.'+str(config['versionCode']) if kind=='manga' else config['versionName'],
            'medium':module['medium'],'extensionLib':module['api'],
            'entryPoints':[f'example.placeholder.{kind}.{kind.title() if kind!="tv" else "Tv"}Factory'],
            'sources':[{'id':module['sourceId'],'name':module['name'],'language':config['language']}] if kind in {'video', 'manga', 'tv'} else [],
            'hashes':{}}
        if kind not in {'video', 'manga'}:
            descriptor['minHostVersionCode'] = config['minimumHostVersionCode']
        if kind == 'guide':
            descriptor['guide'] = {'api': 1, 'capabilities': ['episode-guides.v1'],
                'descriptions': {'en': 'Synthetic episode-guide provider for integration verification.', 'it': 'Provider dimostrativo per verificare le guide degli episodi.'}}
        if kind == 'addon':
            descriptor['addon'] = {'api': 1, 'activation': 'more_action',
                'actionLabel': {'en': 'Open demo', 'it': 'Apri demo'},
                'actionSummary': {'en': 'Verify the hosted addon', 'it': 'Verifica l’addon integrato'},
                'descriptions': {'en': 'Component-free addon example. It does not start background work.', 'it': 'Esempio di addon senza componenti Android e senza attività in background.'}}
        (assets/'nyanime/package-v1.json').write_text(json.dumps(descriptor,indent=2)+'\n',encoding='utf-8')
        if kind in {'video','manga'}:
            def home(home_id,title,format_name=None):
                return {'id':home_id,'title':title,'source':{'name':module['name'],'lang':config['language']},
                    'defaults':{'Format':format_name} if format_name else {},
                    'browseFilters':['Genre','Format','Order','Published date'] if kind=='video' else ['Genre','Order','Published date'],
                    'sections':[{'id':'featured','title':'Demo highlights','layout':'featured','filters':{'Order':'Popular'}},
                        {'id':'latest','title':'Recently published demos','filters':{'Order':'Latest'}},
                        {'id':'by-date','title':'Published on a date','filters':{'Order':'Latest'},'dateFilter':'Published date'}],
                    'search':{'id':'search','title':'Search demos','filters':{}},'categories':{'filter':'Genre','exclude':['All']}}
            homes=[home('demo-animation','DEMO Animation','Animation'),home('demo-cartoons','DEMO Cartoons','Cartoons')] if kind=='video' else [home('demo-manga','DEMO Manga')]
            target=assets/'aniyomi/home-v1.json'
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(json.dumps({'version':1,'homes':homes},indent=2)+'\n',encoding='utf-8')
        image=root/'website/images/icon.png'
        if image.exists():
            target=assets/'nyanime/rin-icon'; target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(image,target)
    print('Generated package metadata and Home contracts. Video declares two independent Home categories.')

if __name__=='__main__':
    configure()
