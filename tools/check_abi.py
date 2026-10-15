#!/usr/bin/env python3
"""Verify compiled base extension classes against a pinned JVM API profile, including inherited members.

Run against compiled .class directories/JARs before D8, not Kotlin source text.
Optional host-specific classes must live under an explicit separate namespace.
"""
import argparse
import hashlib
import json
import re
import struct
import zipfile
from pathlib import Path

API_PREFIXES = ('eu/kanade/tachiyomi/source/', 'eu/kanade/tachiyomi/animesource/',
                'eu/kanade/tachiyomi/network/', 'nyanime/extension/api/',
                'nyanime/news/api/', 'nyanime/tv/api/', 'nyanime/addon/api/')


class Reader:
    def __init__(self, data):
        self.data, self.pos = data, 0
    def take(self, n):
        value = self.data[self.pos:self.pos+n]
        if len(value) != n:
            raise ValueError('Truncated JVM class')
        self.pos += n
        return value
    def number(self, size):
        return int.from_bytes(self.take(size), 'big')


def class_file(data):
    reader = Reader(data)
    if reader.take(4) != b'\xca\xfe\xba\xbe':
        raise ValueError('Not a JVM class')
    reader.take(4)
    count = reader.number(2)
    pool = [None] * count
    index = 1
    while index < count:
        tag = reader.number(1)
        if tag == 1:
            pool[index] = reader.take(reader.number(2)).decode('utf-8', errors='replace')
        elif tag in (7, 8, 16, 19, 20):
            pool[index] = (tag, reader.number(2))
        elif tag in (9, 10, 11, 12, 17, 18):
            pool[index] = (tag, reader.number(2), reader.number(2))
        elif tag == 15:
            reader.take(3)
        elif tag in (3, 4):
            reader.take(4)
        elif tag in (5, 6):
            reader.take(8)
            index += 1
        else:
            raise ValueError('Unknown JVM constant tag: ' + str(tag))
        index += 1
    def name(slot):
        return pool[pool[slot][1]]
    reader.number(2)
    own = name(reader.number(2))
    parent = reader.number(2)
    parents = ([name(parent)] if parent else []) + [name(reader.number(2)) for _ in range(reader.number(2))]
    members = set()
    declared_types = []
    for kind in ('field', 'method'):
        for _ in range(reader.number(2)):
            access, member, descriptor = reader.number(2), pool[reader.number(2)], pool[reader.number(2)]
            declared_types.extend(re.findall(r'L([^;]+);', descriptor))
            if access & (1 | 4):
                members.add((kind, member, descriptor))
            for _ in range(reader.number(2)):
                reader.take(2)
                reader.take(reader.number(4))
    refs = []
    for constant in pool:
        if isinstance(constant, tuple) and constant[0] in (9, 10, 11):
            _, owner, signature = constant
            _, member, descriptor = pool[signature]
            refs.append((name(owner), 'field' if constant[0] == 9 else 'method', pool[member], pool[descriptor]))
    types = [name(i) for i, item in enumerate(pool) if isinstance(item, tuple) and item[0] == 7]
    types.extend(declared_types)
    for _, _, _, descriptor in refs:
        types.extend(re.findall(r'L([^;]+);', descriptor))
    types = [item[1:-1] if item.startswith('L') and item.endswith(';') else item for item in types]
    types = [item.lstrip('[').removeprefix('L').removesuffix(';') if item.startswith('[') else item for item in types]
    return {'name': own, 'parents': parents, 'members': members, 'refs': refs, 'types': types}


def read_classes(path):
    path = Path(path)
    if path.is_dir():
        return [class_file(item.read_bytes()) for item in path.rglob('*.class')]
    with zipfile.ZipFile(path) as archive:
        return [class_file(archive.read(name)) for name in archive.namelist() if name.endswith('.class')]


def verify(implementations, baselines, optional_prefix=()):
    api = {item['name']: item for item in baselines}
    failures = []
    def resolves(owner, signature, visited=None):
        visited = set() if visited is None else visited
        if owner in visited or owner not in api:
            return False
        visited.add(owner)
        target = api[owner]
        if signature in target['members']:
            return True
        if signature[1] == '<init>':
            return False
        return any(resolves(parent, signature, visited) for parent in target['parents'])
    for implementation in implementations:
        if implementation['name'].startswith(tuple(optional_prefix)):
            continue
        for parent in implementation['parents'] + implementation.get('types', []):
            if parent.startswith(API_PREFIXES) and parent not in api:
                failures.append(implementation['name'] + ': missing base type ' + parent)
        for owner, kind, name, descriptor in implementation['refs']:
            if owner.startswith(API_PREFIXES) and not resolves(owner, (kind, name, descriptor)):
                failures.append(implementation['name'] + ': missing ' + owner + '.' + name + descriptor)
    return sorted(set(failures))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=['aniyomi-video-api', 'aniyomi-manga-api', 'nyanime'], required=True)
    parser.add_argument('--classes', type=Path, required=True)
    parser.add_argument('--sdk', type=Path, default=Path(__file__).resolve().parents[1] / 'sdk')
    parser.add_argument('--optional-prefix', action='append', default=[])
    args = parser.parse_args()
    if args.profile == 'nyanime':
        lock = json.loads((args.sdk / 'sdk-lock.json').read_text())
        profiles = lock['modules']
        identity = 'Nyanime ' + lock['sourceTag'] + ' at ' + lock['hostRevision']
    else:
        lock = json.loads((args.sdk / 'portable-sdk-lock.json').read_text())
        profiles = {args.profile: lock['modules'][args.profile]}
        identity = profiles[args.profile]['coordinate']
    baseline = []
    for name, record in profiles.items():
        jar = args.sdk / (name + '.jar')
        if hashlib.sha256(jar.read_bytes()).hexdigest() != record['sha256']:
            raise ValueError('API JAR differs from the pinned profile: ' + name)
        baseline.extend(read_classes(jar))
    failures = verify(read_classes(args.classes), baseline, args.optional_prefix)
    if failures:
        raise SystemExit('\n'.join(failures))
    print('JVM API references match ' + identity + '. Device verification is still required.')


if __name__ == '__main__':
    main()
