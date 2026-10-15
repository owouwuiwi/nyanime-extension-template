#!/usr/bin/env python3
"""Export compile-only APIs from a Nyanime source checkout; never reads signing keys."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MODULES={'source-api':'source-api','core-common':'core/common','news-api':'news-api','tv-api':'tv-api','addon-api':'addon-api'}

def export(host, build=False):
    host=Path(host).resolve()
    if not (host/'source-api/src').is_dir():
        raise SystemExit('Not a Nyanime checkout: source-api/src is missing.')
    if build:
        import os
        wrapper='gradlew.bat' if os.name=='nt' else './gradlew'
        subprocess.run([str(host/wrapper),*(':'+value.replace('/',':')+':assembleRelease' for value in MODULES.values()),'--max-workers=2'],cwd=host,check=True)
    sdk=ROOT/'sdk'
    sdk.mkdir(exist_ok=True)
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=host,text=True).strip()
    records={}
    for name,module in MODULES.items():
        candidates=[host/module/'build/intermediates/aar_main_jar/release/syncReleaseLibJars/classes.jar',
                    host/module/'build/intermediates/compile_library_classes_jar/release/bundleLibCompileToJarRelease/classes.jar',
                    host/module/'build/intermediates/runtime_library_classes_jar/release/bundleLibRuntimeToJarRelease/classes.jar']
        source=next((path for path in candidates if path.is_file()),None)
        if source is None:
            raise SystemExit(f'{module} API has not been built. Re-run with --build (no app APK is built).')
        target=sdk/(name+'.jar')
        shutil.copyfile(source,target)
        tracked=subprocess.check_output(['git','ls-files',module+'/src',module+'/build.gradle.kts'],cwd=host,text=True).splitlines()
        tracked += subprocess.check_output(['git','ls-files','--others','--exclude-standard',module+'/src'],cwd=host,text=True).splitlines()
        digest=hashlib.sha256()
        for path in sorted(set(tracked)):
            file=host/path
            if file.is_file():
                digest.update(path.encode()+b'\0'+file.read_bytes()+b'\0')
                if '/src/' in path.replace('\\','/'):
                    reference=sdk/'sources'/name/Path(path).relative_to(module)
                    reference.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copyfile(file,reference)
        records[name]={'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'sourceSha256':digest.hexdigest()}
    properties=dict(line.split('=',1) for line in (host/'release.properties').read_text().splitlines() if '=' in line and not line.startswith('#'))
    lock={'sourceTag':'v'+properties['versionName'],'schema':1,'hostRevision':revision,'source':'https://github.com/owouwuiwi/nyanime-source',
          'compileOnly':True,'freshBuild':build,'modules':records}
    (sdk/'sdk-lock.json').write_text(json.dumps(lock,indent=2)+'\n',encoding='utf-8')
    for name in ['gradlew','gradlew.bat','gradle/wrapper/gradle-wrapper.jar','gradle/wrapper/gradle-wrapper.properties']:
        target=ROOT/name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(host/name,target)
    (ROOT/'gradlew').chmod(0o755)
    shutil.copyfile(host/'LICENSE',ROOT/'LICENSE')
    print('SDK ready. API JARs are compile-only; they must not be bundled into extension DEX.')
    if not build:
        print('Existing build outputs reused. For reproducible SDK publication, export with --build on a clean pinned checkout.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host',type=Path,required=True)
    parser.add_argument('--build',action='store_true',help='Build API modules only before exporting')
    args=parser.parse_args()
    export(args.host,args.build)
