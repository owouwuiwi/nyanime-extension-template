#!/usr/bin/env python3
"""Read-only legacy helpers and shared APK signing primitives. New releases use sign_apk.py."""
import argparse
import json
import struct
from datetime import datetime, timedelta, timezone
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

ROOT=Path(__file__).resolve().parents[1]

# D8 may emit this marker annotation for desugared lambdas. It is compiler
# metadata, not a bundled host API or shared runtime. Do not allow its package.
COMPILER_MARKERS={'Lcom/android/tools/r8/annotations/LambdaMethod;'}

def validate_classes(classes):
    unexpected=[descriptor for descriptor in classes if not descriptor.startswith('Lexample/placeholder/') and descriptor not in COMPILER_MARKERS]
    if unexpected:
        raise ValueError('Host APIs or shared libraries were bundled. Keep them compileOnly. Unexpected: '+unexpected[0])

def defined_classes(data):
    if not data.startswith(b'dex\n'): raise ValueError('Not a DEX file')
    strings_size,strings_off,types_size,types_off=struct.unpack_from('<4I',data,56)
    count,offset=struct.unpack_from('<2I',data,96)
    def string(index):
        if not 0<=index<strings_size: raise ValueError('Invalid DEX string index')
        at=struct.unpack_from('<I',data,strings_off+index*4)[0]
        for _ in range(5):
            value=data[at];at+=1
            if value<128:break
        else:raise ValueError('Invalid DEX string length')
        return data[at:data.index(0,at)].decode('utf-8')
    result=[]
    for index in range(count):
        class_id=struct.unpack_from('<I',data,offset+index*32)[0]
        if class_id>=types_size:raise ValueError('Invalid DEX class index')
        result.append(string(struct.unpack_from('<I',data,types_off+class_id*4)[0]))
    return result

def development_key():
    directory=ROOT/'.local';directory.mkdir(exist_ok=True)
    keyfile,certfile=directory/'publisher-key.pem',directory/'publisher-cert.der'
    if not keyfile.exists() and not certfile.exists():
        key=rsa.generate_private_key(public_exponent=65537,key_size=3072)
        subject=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'Local placeholder extension publisher')])
        now=datetime.now(timezone.utc)
        certificate=x509.CertificateBuilder().subject_name(subject).issuer_name(subject).public_key(key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(minutes=5)).not_valid_after(now+timedelta(days=3650)).sign(key,hashes.SHA256())
        keyfile.write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
        keyfile.chmod(0o600)
        certfile.write_bytes(certificate.public_bytes(serialization.Encoding.DER))
    if not keyfile.exists() or not certfile.exists():raise ValueError('Local signing identity is incomplete. Restore your existing key/certificate pair; do not silently replace it.')
    return keyfile,certfile

def pack(kind,apk,keyfile,certfile,output):
    raise ValueError("New extensions are signed APKs. Use tools/sign_apk.py.")

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind',choices=['video','manga','tv'])
    parser.add_argument('--apk',type=Path)
    parser.add_argument('--development',action='store_true',help='Create/reuse your local, gitignored demo publisher identity')
    parser.add_argument('--key',type=Path)
    parser.add_argument('--certificate',type=Path,help='X.509 certificate in DER format')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.development:
        if args.key or args.certificate:parser.error('Use --development OR --key/--certificate')
        key,certificate=development_key()
    else:
        if not args.key or not args.certificate:parser.error('Provide --development or your own --key and --certificate')
        key,certificate=args.key,args.certificate
    apk=args.apk or ROOT/args.kind/f'build/outputs/apk/debug/{args.kind}-debug.apk'
    pack(args.kind,apk,key,certificate,args.output or ROOT/'dist'/f'placeholder-{args.kind}-{json.loads((ROOT/"template.json").read_text())["versionName"]}.rin')
