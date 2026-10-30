#!/usr/bin/env python3
"""Rebuild inverse MixColumns seeds from preserved evidence, without network/search."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
import tarfile

SEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SEARCH.parent))
from search.target import matrix_sha256, ncff, normalise, verify

REPOSITORY = SEARCH.parent
LOCAL = SEARCH / 'targets/local/invmixcolumns'
NIST = SEARCH / 'targets/nist/invmixcolumns'
SEEDS = SEARCH / 'targets/seeds/invmixcolumns'
TARGET = SEARCH / 'targets/invmixcolumns.json'
CATALOG = NIST / 'source_catalog.json'
INDICES = (1571840, 1571880, 1571900, 1572350, 1572381, 1573055)
OFFICIAL_POINTS = ((119, 5), (107, 6), (102, 7), (96, 8))
LOCAL_POINTS = (('invmc_cascade_95_depth9', 95, 9),
                ('invmc_cascade_91_depth14', 91, 14),
                ('invmc_alt_89_depth16', 89, 16)) + tuple(
                    (f'invmc_bigen_88_depth19_idx{index}', 88, 19) for index in INDICES)
INVERSE = ((14, 11, 13, 9), (9, 14, 11, 13), (13, 9, 14, 11), (11, 13, 9, 14))
FORWARD = ((2, 3, 1, 1), (1, 2, 3, 1), (1, 1, 2, 3), (3, 1, 1, 2))


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def relative(path):
    return Path(path).relative_to(SEARCH).as_posix()


def gf_mul(a, b):
    result = 0
    for _ in range(8):
        if b & 1:
            result ^= a
        a = ((a << 1) ^ (0x11b if a & 0x80 else 0)) & 255
        b >>= 1
    return result


def scalar_mix(word, coefficients=INVERSE):
    values = [(word >> (8 * byte)) & 255 for byte in range(4)]
    result = 0
    for out, row in enumerate(coefficients):
        value = 0
        for coefficient, byte in zip(row, values):
            value ^= gf_mul(coefficient, byte)
        result |= value << (8 * out)
    return result


def reconstruct_rows():
    columns = [scalar_mix(1 << bit) for bit in range(32)]
    return [sum(((column >> out) & 1) << bit for bit, column in enumerate(columns)) for out in range(32)]


def expand(spec):
    names = []
    for token in spec.split():
        if ':' not in token:
            names.append(token)
            continue
        match = re.fullmatch(r'([A-Za-z_]+)(\d+):([A-Za-z_]+)(\d+)', token)
        if not match or match[1] != match[3] or int(match[2]) > int(match[4]):
            raise ValueError('Invalid NCFF wire range: ' + token)
        names.extend(match[1] + str(index) for index in range(int(match[2]), int(match[4]) + 1))
    return names


def parse_ncff(text):
    inputs = outputs = None
    active, operations = False, []
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith('Inputs:'):
            inputs = expand(line.partition(':')[2])
        elif line.startswith('Outputs:'):
            outputs = expand(line.partition(':')[2])
        elif line == 'begin SLP':
            active = True
        elif line == 'end SLP':
            active = False
        elif active and line and not line.startswith(('%', '#')):
            parts = line.split()
            if len(parts) != 4 or parts[0] != 'XOR':
                raise ValueError('Inverse seed is not an XOR-only NCFF program')
            operations.append(parts[1:])
    if inputs is None or outputs is None or len(inputs) != 32 or len(outputs) != 32 or len(set(inputs)) != 32:
        raise ValueError('Inverse NCFF requires an explicit 32-input, 32-output interface')
    names = {name: index for index, name in enumerate(inputs)}
    gates = []
    for out, a, b in operations:
        if out in names or a not in names or b not in names:
            raise ValueError('Non-SSA or non-topological NCFF instruction')
        gates.append([names[a], names[b]])
        names[out] = 32 + len(gates) - 1
    if any(out not in names for out in outputs):
        raise ValueError('NCFF is missing a declared output')
    return {'benchmark': 'invmixcolumns', 'inputCount': 32, 'gates': gates,
            'outputSignals': [names[name] for name in outputs]}


def assert_equivalent(circuit, target, count, depth):
    checked = verify(circuit, target)
    if not checked['equivalent'] or (checked['gate_count'], checked['depth']) != (count, depth):
        raise ValueError('Seed differs from its declared inverse MixColumns metrics')
    if checked['dead_gates']:
        raise ValueError('Seed has unused gates')
    return checked


class Preserver:
    def __init__(self):
        self.files = {}

    def preserve(self, repository_path, expected=None):
        path = Path(repository_path)
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('Invalid repository evidence path')
        original = REPOSITORY / path
        portable = LOCAL / 'repository' / path
        if original.is_file():
            raw = original.read_bytes()
            if expected and hashlib.sha256(raw).hexdigest() != expected:
                raise ValueError('Original evidence hash mismatch: ' + str(path))
            portable.parent.mkdir(parents=True, exist_ok=True)
            portable.write_bytes(raw)
        elif not portable.is_file():
            raise FileNotFoundError('Missing original and portable evidence: ' + str(path))
        actual = sha256(portable)
        if expected and actual != expected:
            raise ValueError('Portable evidence hash mismatch: ' + str(path))
        entry = {'repository_path': path.as_posix(), 'portable_path': relative(portable), 'sha256': actual,
                 'size_bytes': portable.stat().st_size}
        self.files[path.as_posix()] = entry
        return entry

    def portable(self, entry):
        return SEARCH / entry['portable_path']


def _source_references(card):
    refs = []
    for item in card['source_code']['files']:
        refs.append((item['archive'], item['archive_sha256']))
    for item in card['configuration'].values():
        if isinstance(item, dict) and item.get('path') and item.get('sha256'):
            refs.append((item['path'], item['sha256']))
    item = card['source_provenance_card']
    refs.append((item['path'], item['sha256']))
    for path in card['discovery']['evidence']:
        refs.append((path, None))
    for path in card['starting_point'].get('inputs', []):
        if '::' not in path:
            refs.append((path, None))
    return refs


def build():
    preserver = Preserver()
    benchmark_ref = preserver.preserve('benchmarks/invmixcolumns.json')
    benchmark = json.loads(preserver.portable(benchmark_ref).read_text())
    rows = reconstruct_rows()
    if rows != benchmark['rows']:
        raise ValueError('Independent GF(2^8) matrix does not match preserved benchmark')
    packed_hash = hashlib.sha256(b''.join(row.to_bytes(4, 'little') for row in rows)).hexdigest()
    if packed_hash != benchmark['matrix_sha256']:
        raise ValueError('Legacy packed-le32 matrix hash mismatch')
    for bit in range(32):
        value = 1 << bit
        if scalar_mix(scalar_mix(value), FORWARD) != value or scalar_mix(scalar_mix(value, FORWARD)) != value:
            raise ValueError('Inverse/forward composition failed')
    catalog = json.loads(CATALOG.read_text())
    for entry in catalog['files']:
        path = SEARCH / entry['portable_path']
        raw = path.read_bytes()
        blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        if sha256(path) != entry['sha256'] or blob != entry['git_blob_sha1']:
            raise ValueError('Pinned official bytes changed')
    page = catalog['website']
    if sha256(SEARCH / page['portable_path']) != page['sha256']:
        raise ValueError('Preserved NIST website bytes changed')
    target = {'id': 'invmixcolumns', 'name': 'AES Inverse MixColumns (one column, FIPS LSB-first)',
              'input_count': 32, 'output_count': 32, 'rows': rows, 'matrix_sha256': matrix_sha256(32, rows),
              'affine_output_constants': [0] * 32,
              'input_bit_order': 'x_(8*b+r): bit r (LSB=0) of byte b, b=0..3',
              'output_bit_order': 'y_(8*b+r): bit r (LSB=0) of byte b, b=0..3',
              'scope': 'One AES inverse MixColumns column over GF(2^8), polynomial0x11b, XOR gates only.',
              'nist_commit': catalog['commit'],
              'matrix_source': {'kind': 'independently rebuilt FIPS-197 GF(2^8) matrix; equals preserved repository benchmark',
                  'specification': benchmark['specification'], 'byte_coefficients': INVERSE,
                  'polynomial': '0x11b', 'benchmark': benchmark_ref,
                  'generic_matrix_encoding': 'SHA256 of canonical JSON {input_count:32,rows:[...]} without trailing newline',
                  'legacy_matrix_encoding': benchmark['matrix_encoding'], 'legacy_packed_le32_sha256': packed_hash,
                  'legacy_hash_is_generic_hash': False,
                  'official_catalog': {'path': relative(CATALOG), 'sha256': sha256(CATALOG)}},
              'seed_order_policy': '119@5,107@6,102@7,96@8,local95@9,local91@14,local89@16,then six local88@19 in increasing corpus index',
              'seeds': []}
    official_checks = []
    for entry in catalog['files']:
        checked = assert_equivalent(parse_ncff((SEARCH / entry['portable_path']).read_text()), target,
                                    entry['gate_count'], entry['depth'])
        official_checks.append({'path': entry['portable_path'], 'sha256': entry['sha256'], 'verification': checked})
    official_check_path = NIST / 'verification.json'
    save(official_check_path, {'target_id': target['id'], 'matrix_sha256': target['matrix_sha256'], 'files': official_checks})
    origins = []
    archive_refs = {}

    def emit(seed_id, circuit, count, depth, source_kind, original_files, historical, sources, original_json_verification=None):
        checked = assert_equivalent(circuit, target, count, depth)
        normalized = normalise(circuit['gates'], target)
        normalized_checked = assert_equivalent(normalized, target, count, depth)
        exported = ncff(normalized, target)
        replay = parse_ncff(exported)
        replay_checked = assert_equivalent(replay, target, count, depth)
        if replay['gates'] != normalized['gates'] or replay['outputSignals'] != normalized['outputSignals']:
            raise ValueError('Normalized NCFF does not preserve the exact circuit')
        origin_path = LOCAL / 'records' / seed_id / 'origin.json'
        origin = {'schema': 1, 'seed_id': seed_id, 'target_id': target['id'], 'source_kind': source_kind,
                  'generic_matrix_sha256': target['matrix_sha256'], 'legacy_packed_le32_sha256': packed_hash,
                  'original_files': original_files, 'source_references': sources, 'historical': historical,
                  'original_verification': checked, 'original_json_verification': original_json_verification,
                  'normalized_verification': normalized_checked,
                  'ncff_verification': replay_checked,
                  'normalization': 'Reemit live unique values with generic target.normalise; metrics unchanged; original bytes preserved separately'}
        save(origin_path, origin)
        normalized['provenance'] = {'source_kind': source_kind, 'origin_manifest': relative(origin_path),
                                    'origin_manifest_sha256': sha256(origin_path),
                                    'historical_discovery_commit': historical.get('discovery_commit')}
        path = SEEDS / (seed_id + '.json')
        save(path, normalized)
        path.with_suffix('.ncff').write_text(exported)
        save(path.with_suffix('.verification.json'), verify(normalized, target))
        entry = {'path': relative(path), 'gates': count, 'depth': depth, 'source_kind': source_kind,
                 'sha256': sha256(path), 'circuit_sha256': normalized_checked['circuit_sha256'],
                 'dag_sha256': normalized_checked['dag_sha256'], 'value_set_sha256': normalized_checked['value_set_sha256'],
                 'ncff_path': relative(path.with_suffix('.ncff')), 'ncff_sha256': sha256(path.with_suffix('.ncff')),
                 'verification_path': relative(path.with_suffix('.verification.json')),
                 'verification_sha256': sha256(path.with_suffix('.verification.json')),
                 'origin_manifest': relative(origin_path), 'origin_manifest_sha256': sha256(origin_path)}
        target['seeds'].append(entry)
        origins.append({'path': relative(origin_path), 'sha256': sha256(origin_path)})

    bypoint = {(item['gate_count'], item['depth']): item for item in catalog['files']}
    for count, depth in OFFICIAL_POINTS:
        entry = bypoint[count, depth]
        circuit = parse_ncff((SEARCH / entry['portable_path']).read_text())
        emit(f'nist_g{count}_d{depth}', circuit, count, depth, 'official NIST circuit', [entry],
             {'repository_commit': catalog['commit'], 'discovery_commit': None, 'execution': None,
              'randomness': None, 'limits': ['Pinned source commit is not asserted to be a historical discovery commit.']},
             [{'path': relative(CATALOG), 'sha256': sha256(CATALOG)}])

    for stem, count, depth in LOCAL_POINTS:
        prefix = 'records/invmixcolumns/published/' + stem
        card_ref = preserver.preserve(prefix + '.record.json')
        card = json.loads(preserver.portable(card_ref).read_text())
        json_ref = preserver.preserve(card['circuit']['json'], card['circuit']['json_sha256'])
        ncff_ref = preserver.preserve(card['circuit']['ncff'], card['circuit']['ncff_sha256'])
        original = json.loads(preserver.portable(json_ref).read_text())
        circuit = parse_ncff(preserver.portable(ncff_ref).read_text())
        if circuit['gates'] != original['gates']:
            raise ValueError('Original JSON and exact NCFF operand pairs differ: ' + stem)
        for key in ('outputSignals', 'outputs', 'output_signals'):
            outputs = original.get(key, original.get('provenance', {}).get(key))
            if outputs is not None:
                if isinstance(outputs, dict):
                    outputs = [outputs[str(index)] for index in range(32)]
                if outputs != circuit['outputSignals']:
                    raise ValueError('Original declared output mapping differs from NCFF')
        sources = []
        for path, expected in _source_references(card):
            sources.append(preserver.preserve(path, expected))
        for source in card['source_code']['files']:
            archive = preserver.preserve(source['archive'], source['archive_sha256'])
            archive_refs[source['archive']] = archive
            with tarfile.open(preserver.portable(archive), 'r:gz') as tar:
                raw = tar.extractfile(source['member']).read()
            if hashlib.sha256(raw).hexdigest() != source['sha256']:
                raise ValueError('Producing source archive member hash mismatch')
        original_json_checked = assert_equivalent(original, target, count, depth)
        if original_json_checked['outputs'] != circuit['outputSignals']:
            raise ValueError('Original JSON replay outputs differ from exact NCFF')
        kind = 'local deterministic inverse derivation from forward corpus; not NIST' if count == 88 else 'local search record; not NIST'
        history = {'discovery_commit': card['source_code']['discovery_commit'],
                   'execution': card['execution'], 'randomness': card['randomness'],
                   'discovery': card['discovery'], 'provenance_class': card['provenance_class'],
                   'limits': card['limits'], 'source_code': card['source_code']}
        emit(stem, circuit, count, depth, kind, [json_ref, ncff_ref, card_ref], history, sources, original_json_checked)

    # Preserve both archive manifests, so the portable copy retains their full byte/commit mapping.
    for path in ('sources/invmixcolumns-source-manifest.json', 'sources/invmixcolumns-e27-manifest.json'):
        preserver.preserve(path)
    six = target['seeds'][-6:]
    if len({entry['dag_sha256'] for entry in six}) != 6 or len({entry['value_set_sha256'] for entry in six}) != 6:
        raise ValueError('The six published88@19 seeds are not genuinely distinct')
    if len(target['seeds']) != 13:
        raise ValueError('Wrong inverse seed count')
    save(TARGET, target)
    manifest = {'schema': 1, 'target': {'path': relative(TARGET), 'sha256': sha256(TARGET)},
                'matrix_sha256': target['matrix_sha256'], 'legacy_packed_le32_sha256': packed_hash,
                'catalog': {'path': relative(CATALOG), 'sha256': sha256(CATALOG)},
                'official_verification': {'path': relative(official_check_path), 'sha256': sha256(official_check_path)},
                'preserved_files': list(preserver.files.values()), 'origins': origins,
                'portable_source_archives': list(archive_refs.values()),
                'seed_order': [entry['path'] for entry in target['seeds']],
                'historical_limits': ['Unknown discovery commits, CPU models and RNG states remain null in copied record cards and origins.',
                    'Imported circuits are starting points, not new search discoveries.',
                    'Six88@19 circuits are deterministic derivatives of forward-corpus rows, not independent inverse-search discoveries.']}
    save(LOCAL / 'import_manifest.json', manifest)
    return target, manifest


if __name__ == '__main__':
    target, manifest = build()
    print(json.dumps({'target': target['id'], 'matrix_sha256': target['matrix_sha256'],
                      'legacy_matrix_sha256': target['matrix_source']['legacy_packed_le32_sha256'],
                      'seeds': [(entry['gates'], entry['depth']) for entry in target['seeds']],
                      'portable_evidence_files': len(manifest['preserved_files'])}, indent=2))
