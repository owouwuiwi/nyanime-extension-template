import contextlib
import hashlib
import io
import json
import struct
import sys
import tempfile
import unittest
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.x509.oid import NameOID

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from configure import configure
from verify_rin import verify
from pack import defined_classes, validate_classes


class ConfigurationTest(unittest.TestCase):
    def config(self, change=None):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        config = json.loads((ROOT / 'template.json').read_text())
        if change:
            change(config)
        (root / 'template.json').write_text(json.dumps(config))
        return root, config

    def test_two_home_categories_are_declared_and_scoped(self):
        root, config = self.config()
        with contextlib.redirect_stdout(io.StringIO()):
            configure(root)
        declaration = json.loads((root / 'video/src/main/assets/aniyomi/home-v1.json').read_text())
        self.assertEqual(['demo-animation', 'demo-cartoons'], [home['id'] for home in declaration['homes']])
        self.assertEqual(['Animation', 'Cartoons'], [home['defaults']['Format'] for home in declaration['homes']])
        for home in declaration['homes']:
            self.assertEqual(config['modules']['video']['name'], home['source']['name'])
            self.assertEqual('Genre', home['categories']['filter'])

    def test_duplicate_source_ids_rejected_before_writing(self):
        def change(config):
            config['modules']['video']['sourceId'] = config['modules']['manga']['sourceId']
        root, _ = self.config(change)
        with self.assertRaises(ValueError):
            configure(root)
        self.assertFalse((root / 'video').exists())

    def test_invalid_origin_identity_and_build_values_are_rejected(self):
        changes = [lambda c: c.update(baseUrl='http://unsafe.invalid/'),
                   lambda c: c.update(baseUrl='https://user:secret@unsafe.invalid/'),
                   lambda c: c.update(baseUrl='https://fixture.invalid/?private=x'),
                   lambda c: c.update(versionCode=0),
                   lambda c: c.update(versionName='1.0"bad'),
                   lambda c: c.update(language='English'),
                   lambda c: c['modules']['video'].update(sourceId=2**63),
                   lambda c: c['modules']['tv'].update(package='../escape')]
        for change in changes:
            root, _ = self.config(change)
            with self.subTest(root=root), self.assertRaises(ValueError):
                configure(root)
            self.assertFalse((root / 'video').exists())

    def test_generated_fixture_media_matches_its_hash_manifest(self):
        manifest = json.loads((ROOT / 'website/assets-manifest.json').read_text())
        self.assertEqual('CC0-1.0', manifest['license'])
        self.assertGreater(len(manifest['assets']), 30)
        for name, digest in manifest['assets'].items():
            self.assertEqual(digest, hashlib.sha256((ROOT / 'website' / name).read_bytes()).hexdigest(), name)


class SignatureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Test publisher')])
        now = datetime.now(timezone.utc)
        cls.certificate = x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(cls.key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now - timedelta(days=1)).not_valid_after(now + timedelta(days=1)).sign(cls.key, hashes.SHA256()).public_bytes(serialization.Encoding.DER)
        cls.fingerprint = hashlib.sha256(cls.certificate).hexdigest()

    def archive(self, alteration=None):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        output = Path(temporary.name) / 'sample.rin'
        payload = {'classes.dex': b'opaque fixture for integrity tests'}
        manifest = {'schema': 1, 'medium': 'anime', 'packageName': 'example.fixture.video',
                    'sources': [{'id': 123, 'name': 'Fixture', 'language': 'en'}],
                    'hashes': {name: hashlib.sha256(data).hexdigest() for name, data in payload.items()}}
        raw = json.dumps(manifest).encode()
        entries = dict(payload, **{'manifest.json': raw, 'META-INF/rin.cert': self.certificate,
                                  'META-INF/rin.sig': self.key.sign(raw, padding.PKCS1v15(), hashes.SHA256())})
        if alteration:
            alteration(entries)
        with zipfile.ZipFile(output, 'w') as archive:
            for name, data in entries.items():
                archive.writestr(name, data)
        return output

    def test_signature_hashes_and_expected_publisher(self):
        self.assertEqual(self.fingerprint, verify(self.archive(), self.fingerprint)['publisher'])

    def test_wrong_publisher_is_rejected(self):
        with self.assertRaises(ValueError):
            verify(self.archive(), '0' * 64)

    def test_tampered_payload_is_rejected(self):
        with self.assertRaises(ValueError):
            verify(self.archive(lambda e: e.update({'classes.dex': b'changed'})))

    def test_tampered_manifest_or_signature_is_rejected(self):
        for name in ['manifest.json', 'META-INF/rin.sig']:
            with self.subTest(name=name), self.assertRaises(InvalidSignature):
                verify(self.archive(lambda e: e.update({name: e[name] + b'changed'})))

    def test_unsigned_or_unsafe_entries_are_rejected(self):
        for name in ['assets/unlisted', '../escape', '/absolute']:
            with self.subTest(name=name), self.assertRaises(ValueError):
                verify(self.archive(lambda e: e.update({name: b'extra'})))

    def test_missing_payload_is_rejected(self):
        with self.assertRaises(ValueError):
            verify(self.archive(lambda e: e.pop('classes.dex')))

    def test_dex_inspection_reads_defined_classes(self):
        descriptor = b'Lexample/placeholder/Sample;'
        dex = bytearray(160)
        dex[:8] = b'dex\n035\x00'
        struct.pack_into('<4I', dex, 56, 1, 112, 1, 116)
        struct.pack_into('<2I', dex, 96, 1, 120)
        struct.pack_into('<I', dex, 112, 152)
        struct.pack_into('<I', dex, 116, 0)
        struct.pack_into('<I', dex, 120, 0)
        dex[152:] = bytes([len(descriptor)]) + descriptor + b'\x00'
        self.assertEqual([descriptor.decode()], defined_classes(bytes(dex)))

    def test_runtime_classes_are_rejected_but_exact_compiler_marker_is_allowed(self):
        own = 'Lexample/placeholder/Sample;'
        validate_classes([own, 'Lcom/android/tools/r8/annotations/LambdaMethod;'])
        for descriptor in ['Lkotlin/Unit;', 'Lokhttp3/OkHttpClient;', 'Leu/kanade/tachiyomi/source/Source;',
                           'Lcom/android/tools/r8/Unrelated;']:
            with self.subTest(descriptor=descriptor), self.assertRaises(ValueError):
                validate_classes([own, descriptor])


if __name__ == '__main__':
    unittest.main()
