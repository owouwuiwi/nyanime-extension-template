#!/usr/bin/env python3
"""Verify RIN integrity without executing extension code. This does not establish publisher trust."""
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, ec, padding


def verify(path, publisher=None):
    path = Path(path)
    if not 0 < path.stat().st_size <= 32 * 1024 * 1024:
        raise ValueError('Invalid archive size')
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        if not 4 <= len(names) <= 512 or len(set(names)) != len(names):
            raise ValueError('Duplicate or excessive archive entries')
        if any(entry.is_dir() or '\\' in entry.filename or entry.filename.startswith('/') or
               '..' in entry.filename.split('/') or entry.flag_bits & 1 for entry in entries):
            raise ValueError('Unsafe archive entry')
        if sum(entry.file_size for entry in entries) > 32 * 1024 * 1024:
            raise ValueError('Excessive uncompressed size')
        for name, maximum in [('manifest.json', 65536), ('META-INF/rin.cert', 16384), ('META-INF/rin.sig', 16384)]:
            if not 0 < archive.getinfo(name).file_size <= maximum:
                raise ValueError('Invalid signing metadata size')
        raw = archive.read('manifest.json')
        certificate_bytes = archive.read('META-INF/rin.cert')
        fingerprint = hashlib.sha256(certificate_bytes).hexdigest()
        if publisher is not None and fingerprint != publisher.lower():
            raise ValueError('Unexpected publisher')
        certificate = x509.load_der_x509_certificate(certificate_bytes)
        key = certificate.public_key()
        signature = archive.read('META-INF/rin.sig')
        if isinstance(key, rsa.RSAPublicKey):
            key.verify(signature, raw, padding.PKCS1v15(), hashes.SHA256())
        elif isinstance(key, ec.EllipticCurvePublicKey):
            key.verify(signature, raw, ec.ECDSA(hashes.SHA256()))
        else:
            raise ValueError('Unsupported signing algorithm')
        manifest = json.loads(raw)
        medium = manifest['medium']
        if (manifest['schema'], medium) not in {(1, 'anime'), (1, 'manga'), (2, 'tv')}:
            raise ValueError('This starter verifies source RIN families only')
        if not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_]*(?:\.[a-zA-Z][a-zA-Z0-9_]*)+', manifest['packageName']):
            raise ValueError('Invalid package identity')
        if not manifest['sources'] or len({source['id'] for source in manifest['sources']}) != len(manifest['sources']):
            raise ValueError('Invalid source identities')
        payload = set(names) - {'manifest.json', 'META-INF/rin.cert', 'META-INF/rin.sig'}
        if 'classes.dex' not in payload or payload != set(manifest['hashes']):
            raise ValueError('Unsigned or missing payload')
        for name in payload:
            if not (re.fullmatch(r'classes(?:[2-9][0-9]*)?\.dex', name) or name.startswith('assets/')):
                raise ValueError('Unsupported source payload')
            expected = manifest['hashes'][name]
            if not re.fullmatch('[0-9a-f]{64}', expected) or hashlib.sha256(archive.read(name)).hexdigest() != expected:
                raise ValueError('Payload hash mismatch: ' + name)
        return {'publisher': fingerprint, 'manifest': manifest, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--publisher', help='Expected SHA-256 certificate fingerprint from a trusted channel')
    args = parser.parse_args()
    result = verify(args.archive, args.publisher)
    print('Integrity verified: ' + result['manifest']['packageName'])
    print('Publisher SHA-256: ' + result['publisher'])
    print('Archive SHA-256: ' + result['sha256'])
