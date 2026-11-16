"""Independent field/basis verification and portable inverse-seed provenance."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest

SEARCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SEARCH.parent))
from search.target import matrix_sha256, verify

spec = importlib.util.spec_from_file_location('import_invmixcolumns', SEARCH / 'targets/import_invmixcolumns.py')
importer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(importer)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def polynomial_product(a, b):
    """Independent carryless product then long division, not importer xtime."""
    product = 0
    for bit in range(8):
        if (b >> bit) & 1:
            product ^= a << bit
    while product.bit_length() > 8:
        product ^= 0x11b << (product.bit_length() - 9)
    return product


def scalar(word, inverse=True):
    first = (0x0e, 0x0b, 0x0d, 0x09) if inverse else (0x02, 0x03, 0x01, 0x01)
    source = [(word >> (8 * byte)) & 255 for byte in range(4)]
    output = 0
    for out in range(4):
        byte = 0
        for inp in range(4):
            byte ^= polynomial_product(source[inp], first[(inp - out) % 4])
        output |= byte << (8 * out)
    return output


def evaluate_scalar(circuit, word):
    wires = [(word >> bit) & 1 for bit in range(32)]
    for a, b in circuit['gates']:
        wires.append(wires[a] ^ wires[b])
    return sum(wires[index] << out for out, index in enumerate(circuit['outputSignals']))


class InverseMixColumnsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.target = read(SEARCH / 'targets/invmixcolumns.json')
        cls.manifest = read(SEARCH / 'targets/local/invmixcolumns/import_manifest.json')
        cls.preserved = {entry['repository_path']: entry for entry in cls.manifest['preserved_files']}
        cls.catalog = read(SEARCH / cls.manifest['catalog']['path'])

    def test_fips_orientation_and_independent_32_basis_matrix(self):
        target = self.target
        self.assertEqual((target['input_count'], target['output_count']), (32, 32))
        columns = [scalar(1 << bit) for bit in range(32)]
        rows = [sum(((column >> out) & 1) << inp for inp, column in enumerate(columns)) for out in range(32)]
        self.assertEqual(rows, target['rows'])
        self.assertEqual(rows, importer.reconstruct_rows())
        self.assertEqual(scalar(0x455313db, inverse=False), 0xbca14d8e)
        self.assertEqual(scalar(0xbca14d8e), 0x455313db)

    def test_generic_and_legacy_matrix_hash_encodings_are_distinct(self):
        packed = b''.join(row.to_bytes(4, 'little') for row in self.target['rows'])
        legacy = hashlib.sha256(packed).hexdigest()
        generic = matrix_sha256(32, self.target['rows'])
        self.assertEqual(legacy, 'bea4bc43daff90bd4a19af7763c628f9d422dc795c178523c4fe873221f5b93b')
        self.assertEqual(generic, '7a3774b642e7c92bfaea20e6c1b379c3f4f0f389592f0ab26d089745e40f94a3')
        self.assertNotEqual(legacy, generic)
        self.assertEqual(self.target['matrix_sha256'], generic)
        self.assertEqual(self.target['matrix_source']['legacy_packed_le32_sha256'], legacy)
        benchmark = read(SEARCH / self.preserved['benchmarks/invmixcolumns.json']['portable_path'])
        self.assertEqual(benchmark['rows'], self.target['rows'])
        self.assertEqual(benchmark['matrix_sha256'], legacy)

    def test_forward_inverse_composition(self):
        rng = random.Random(20261028)
        words = [1 << bit for bit in range(32)] + [0, 0xffffffff, 0x01020304, 0xdeadbeef]
        words += [rng.getrandbits(32) for _ in range(32)]
        for word in words:
            self.assertEqual(scalar(scalar(word), inverse=False), word)
            self.assertEqual(scalar(scalar(word, inverse=False)), word)

    def test_exact_thirteen_seed_order_and_strict_normalized_replay(self):
        entries = self.target['seeds']
        expected = [(119, 5), (107, 6), (102, 7), (96, 8), (95, 9), (91, 14), (89, 16)] + [(88, 19)] * 6
        self.assertEqual([(entry['gates'], entry['depth']) for entry in entries], expected)
        self.assertEqual([int(Path(entry['path']).stem.split('idx')[-1]) for entry in entries[-6:]], list(importer.INDICES))
        for entry in entries:
            with self.subTest(path=entry['path']):
                path = SEARCH / entry['path']
                circuit = read(path)
                checked = verify(circuit, self.target)
                self.assertTrue(checked['equivalent'])
                self.assertFalse(checked['outputs_inferred'])
                self.assertEqual(checked['dead_gates'], 0)
                self.assertEqual((checked['gate_count'], checked['depth']), (entry['gates'], entry['depth']))
                self.assertEqual(sha(path), entry['sha256'])
                self.assertEqual(sha(SEARCH / entry['ncff_path']), entry['ncff_sha256'])
                self.assertEqual(read(SEARCH / entry['verification_path']), checked)
                self.assertEqual(sha(SEARCH / entry['verification_path']), entry['verification_sha256'])
                exported = importer.parse_ncff((SEARCH / entry['ncff_path']).read_text())
                self.assertEqual(exported['gates'], circuit['gates'])
                self.assertEqual(exported['outputSignals'], circuit['outputSignals'])
                self.assertTrue(verify(exported, self.target)['equivalent'])
                for bit in range(32):
                    self.assertEqual(evaluate_scalar(circuit, 1 << bit), scalar(1 << bit))

    def test_six_real_distinct_structures_and_value_sets(self):
        six = self.target['seeds'][-6:]
        self.assertEqual(len({entry['dag_sha256'] for entry in six}), 6)
        self.assertEqual(len({entry['value_set_sha256'] for entry in six}), 6)
        self.assertTrue(all('derivation' in entry['source_kind'] and 'not NIST' in entry['source_kind'] for entry in six))

    def test_official_pinned_originals_and_website_comparison(self):
        self.assertEqual(self.catalog['commit'], '8366158a4324ef902ce740f29ddc9f7ebb1018b2')
        self.assertEqual(self.catalog['website']['listed_inverse_points'][0], [121, 5])
        self.assertEqual(self.target['seeds'][0]['gates'], 119)
        self.assertEqual(sha(SEARCH / self.catalog['website']['portable_path']), self.catalog['website']['sha256'])
        for entry in self.catalog['files']:
            path = SEARCH / entry['portable_path']
            raw = path.read_bytes()
            self.assertEqual(sha(path), entry['sha256'])
            self.assertEqual(hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest(), entry['git_blob_sha1'])
            circuit = importer.parse_ncff(raw.decode())
            checked = verify(circuit, self.target)
            self.assertEqual((checked['gate_count'], checked['depth']), (entry['gate_count'], entry['depth']))
            self.assertTrue(checked['equivalent'])
            for bit in range(32):
                self.assertEqual(evaluate_scalar(circuit, 1 << bit), scalar(1 << bit))
        self.assertEqual(sha(SEARCH / self.manifest['official_verification']['path']), self.manifest['official_verification']['sha256'])

    def test_portable_evidence_cards_and_source_archive_member_hashes(self):
        self.assertEqual(sha(SEARCH / self.manifest['target']['path']), self.manifest['target']['sha256'])
        self.assertEqual(sha(SEARCH / self.manifest['catalog']['path']), self.manifest['catalog']['sha256'])
        for entry in self.manifest['preserved_files']:
            path = SEARCH / entry['portable_path']
            self.assertEqual(sha(path), entry['sha256'])
            original = SEARCH.parent / entry['repository_path']
            if original.is_file():
                self.assertEqual(path.read_bytes(), original.read_bytes())
        self.assertEqual(len(self.manifest['portable_source_archives']), 2)
        for entry in self.target['seeds']:
            origin_path = SEARCH / entry['origin_manifest']
            self.assertEqual(sha(origin_path), entry['origin_manifest_sha256'])
            origin = read(origin_path)
            self.assertEqual(origin['historical']['discovery_commit'], None)
            for source in origin['original_files'] + origin['source_references']:
                source_path = source.get('portable_path', source.get('path'))
                self.assertEqual(sha(SEARCH / source_path), source['sha256'])
            if entry['source_kind'] == 'official NIST circuit':
                continue
            card_ref = next(item for item in origin['original_files'] if item['repository_path'].endswith('.record.json'))
            card = read(SEARCH / card_ref['portable_path'])
            self.assertEqual(origin['historical']['execution'], card['execution'])
            self.assertIsNone(card['execution']['cpu_model'])
            self.assertEqual(origin['historical']['randomness'], card['randomness'])
            for source in card['source_code']['files']:
                archive = self.preserved[source['archive']]
                self.assertEqual(archive['sha256'], source['archive_sha256'])
                with tarfile.open(SEARCH / archive['portable_path'], 'r:gz') as tar:
                    raw = tar.extractfile(source['member']).read()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), source['sha256'])
            original = next(item for item in origin['original_files'] if item['repository_path'].endswith('.json') and not item['repository_path'].endswith('.record.json'))
            circuit = read(SEARCH / original['portable_path'])
            self.assertTrue(verify(circuit, self.target)['equivalent'])
            self.assertEqual(verify(circuit, self.target), origin['original_json_verification'])

    def test_portable_importer_rebuilds_without_original_repository(self):
        with tempfile.TemporaryDirectory(prefix='inverse-import-test-') as directory:
            root = Path(directory) / 'search'
            (root / 'targets').mkdir(parents=True)
            shutil.copy2(SEARCH / 'target.py', root / 'target.py')
            shutil.copy2(SEARCH / 'targets/import_invmixcolumns.py', root / 'targets/import_invmixcolumns.py')
            shutil.copytree(SEARCH / 'targets/local/invmixcolumns', root / 'targets/local/invmixcolumns')
            shutil.copytree(SEARCH / 'targets/nist/invmixcolumns', root / 'targets/nist/invmixcolumns')
            process = subprocess.run([sys.executable, str(root / 'targets/import_invmixcolumns.py')],
                                     cwd=directory, capture_output=True, text=True, timeout=30)
            self.assertEqual(process.returncode, 0, process.stderr)
            rebuilt = read(root / 'targets/invmixcolumns.json')
            self.assertEqual(rebuilt, self.target)
            for entry in self.target['seeds']:
                self.assertEqual(sha(root / entry['path']), entry['sha256'])
                self.assertEqual(sha(root / entry['ncff_path']), entry['ncff_sha256'])


if __name__ == '__main__':
    unittest.main()
