#!/usr/bin/env python3
"""Sign an interoperable APK with your owned publisher identity."""
import argparse
import hashlib
import json
import os
import subprocess
import tempfile
import zipfile
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from pack import development_key, defined_classes, validate_classes

ROOT = Path(__file__).resolve().parents[1]


def sign(apk, output, keyfile, certificate_file, build_tools, kind="news"):
    sdk_tools = Path(build_tools)
    suffix = '.exe' if os.name == 'nt' else ''
    java_home = os.environ.get('JAVA_HOME')
    java = str(Path(java_home) / 'bin' / ('java' + suffix)) if java_home else 'java'
    signer = [java, '-jar', str(sdk_tools / 'lib/apksigner.jar')]
    config = json.loads((ROOT / 'template.json').read_text())
    badging = subprocess.check_output([str(sdk_tools / ('aapt2' + suffix)), 'dump', 'badging', str(apk)], text=True)
    if "name='" + config['modules'][kind]['package'] + "'" not in badging.splitlines()[0]:
        raise ValueError('APK package does not match the configured module')
    if 'application-debuggable' in badging:
        raise ValueError('Build the module assembleRelease task first; do not distribute a debuggable APK')
    with zipfile.ZipFile(apk) as archive:
        classes = [descriptor for name in archive.namelist() if name.endswith('.dex') for descriptor in defined_classes(archive.read(name))]
        validate_classes(classes)
        if not any(name.startswith('Lexample/placeholder/'+kind+'/') for name in classes):
            raise ValueError('Extension implementation missing')
    key = serialization.load_pem_private_key(Path(keyfile).read_bytes(), None)
    certificate = x509.load_der_x509_certificate(Path(certificate_file).read_bytes())
    public_format = (serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    if key.public_key().public_bytes(*public_format) != certificate.public_key().public_bytes(*public_format):
        raise ValueError('Certificate and key do not match')
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    private_directory = ROOT / '.local'
    private_directory.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='apk-sign-', dir=private_directory) as task_directory:
        temporary = Path(task_directory)
        private_key = temporary / 'publisher.pk8'
        private_key.write_bytes(key.private_bytes(serialization.Encoding.DER, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        private_key.chmod(0o600)
        aligned = temporary / 'aligned.apk'
        signed = temporary / 'signed.apk'
        subprocess.run([str(sdk_tools / ('zipalign' + suffix)), '-f', '-p', '4', str(apk), str(aligned)], check=True, capture_output=True)
        subprocess.run([*signer, 'sign', '--key', str(private_key), '--cert', str(certificate_file), '--min-sdk-version', '26', '--out', str(signed), str(aligned)], check=True, capture_output=True)
        subprocess.run([*signer, 'verify', '--verbose', str(signed)], check=True, capture_output=True)
        output.write_bytes(signed.read_bytes())
    report = {'file': output.name, 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
              'publisher': hashlib.sha256(Path(certificate_file).read_bytes()).hexdigest(), 'debuggable': False}
    output.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Signed non-debug extension APK: ' + output.name + '; publisher: ' + report['publisher'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind', choices=['video','manga','news','tv','guide','addon'], nargs='?', default='news')
    parser.add_argument('--build-tools', type=Path, required=True)
    parser.add_argument('--apk', type=Path, default=None)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--development', action='store_true')
    parser.add_argument('--key', type=Path)
    parser.add_argument('--certificate', type=Path)
    args = parser.parse_args()
    if args.development:
        if args.key or args.certificate:
            parser.error('Choose --development OR --key/--certificate')
        key, certificate = development_key()
    else:
        if not args.key or not args.certificate:
            parser.error('Supply your publisher key/certificate, or --development for the demo identity')
        key, certificate = args.key, args.certificate
    version = json.loads((ROOT / 'template.json').read_text())['versionName']
    sign(args.apk or ROOT / args.kind / ('build/outputs/apk/release/' + args.kind + '-release-unsigned.apk'), args.output or ROOT / 'dist' / ('placeholder-' + args.kind + '-' + version + '.apk'), key.resolve(), certificate.resolve(), args.build_tools.resolve(), args.kind)
