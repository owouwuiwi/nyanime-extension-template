#!/usr/bin/env python3
"""Create a self-contained developer download, excluding build outputs and signing keys."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOP = {'SDK-NOTICE.md', 'CHANGELOG.md', 'README.md', 'NOTICE', 'LICENSE', 'requirements-tools.txt', 'requirements-site.txt',
       'template.json', 'settings.gradle.kts', 'build.gradle.kts', 'gradle.properties',
       'gradlew', 'gradlew.bat', '.gitignore', 'VERIFICATION.md'}
DIRS = {'video', 'manga', 'news', 'tv', 'guide', 'addon', 'common', 'tools', 'tests', 'docs', 'website', 'gradle', 'sdk', 'web'}


def files():
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if relative.parts[0] not in TOP | DIRS:
            continue
        if any(part in {'build', '__pycache__', 'downloads', '.gradle', '.local', '.tools'} for part in relative.parts):
            continue
        if path.suffix.lower() in {'.pem', '.jks', '.keystore', '.p12', '.pyc', '.der', '.pk8'}:
            raise ValueError('Private signing material must not enter the developer kit: ' + str(relative))
        yield path, relative.as_posix()


def package():
    sdk = ROOT / 'sdk/sdk-lock.json'
    if not sdk.is_file():
        raise ValueError('Export and verify the compile-only SDK first')
    for name, record in json.loads(sdk.read_text())['modules'].items():
        if hashlib.sha256((ROOT / 'sdk' / (name + '.jar')).read_bytes()).hexdigest() != record['sha256']:
            raise ValueError('SDK changed after export: ' + name)
    output = ROOT / 'website/downloads/placeholder-extension-kit.zip'
    output.parent.mkdir(exist_ok=True)
    manifest = {}
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path, name in files():
            data = path.read_bytes()
            manifest[name] = hashlib.sha256(data).hexdigest()
            info = zipfile.ZipInfo('placeholder-extension-kit/' + name)
            info.create_system = 3
            info.external_attr = (0o100755 if name == 'gradlew' else 0o100644) << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED)
        archive.writestr('placeholder-extension-kit/kit-manifest.json', json.dumps(manifest, indent=2) + '\n')
    with zipfile.ZipFile(output) as archive:
        if archive.testzip():
            raise ValueError('Download archive integrity check failed')
    output.with_suffix('.sha256').write_text(hashlib.sha256(output.read_bytes()).hexdigest() + '  ' + output.name + '\n')
    print(f'Developer kit: {len(manifest)} files, {output.stat().st_size} bytes. No keys or build directories.')


if __name__ == '__main__':
    package()
