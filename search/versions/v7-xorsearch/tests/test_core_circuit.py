"""``core.circuit``: the independent verifier, normalisation, hashes and io.

Bit-identity with the reference verifier of earlier versions (verify metrics, dag/circuit/
value-set hashes, normalise gate order, NCFF text) is checked against its recorded outputs
(``tests/data/legacy_golden.json``) on every bundled seed and test circuit; every XOR-only
``circuits/<map>/*.circ.txt`` file must verify against its map; failure reporting and the
zero-row extension are checked on small hand-made circuits.
"""
import hashlib
import json
import os
import unittest

from xorsearch.core.circuit import (Circuit, dag_sha256, ncff, normalise, parse_ncff,
                                    verify)
from xorsearch.core.target import CIRCUITS_DIR, SEARCH_ROOT, Target, catalog, load_target
from xorsearch.core.valueset import ValueSet
from xorsearch.tests.fixtures import DATA

GOLDEN = DATA / 'legacy_golden.json'
VERIFY_FIELDS = ('equivalent', 'gate_count', 'depth', 'dead_gates', 'outputs', 'dag_sha256',
                 'circuit_sha256', 'value_set_sha256')


@unittest.skipUnless(CIRCUITS_DIR.is_dir(), 'no circuits/ next to search/')
class LegacyIdentityTest(unittest.TestCase):
    """Same numbers, hashes and files as the reference verifier of earlier versions."""

    def compare(self, circuit, target, want, cap=None):
        mine = verify(circuit, target, cap=cap)
        self.assertTrue(mine.ok, mine.reason)
        self.assertEqual({k: getattr(mine, k) for k in VERIFY_FIELDS}, want)
        self.assertEqual(dag_sha256(circuit, target), mine.dag_sha256)
        return mine

    def test_all_seeds(self):
        cases = json.loads(GOLDEN.read_text())['cases']
        targets = {}
        for case in cases:
            target = targets.setdefault(case['map'], load_target(case['map']))
            with self.subTest(file=case['file']):
                circuit = Circuit.load(SEARCH_ROOT / case['file'], target.n_inputs)
                v = self.compare(circuit, target, case['verify'], cap=case['verify']['depth'])
                # normalise: identical gates and outputs to the old implementation
                norm = normalise(circuit, target)
                self.assertEqual([list(g) for g in norm.gates], case['normalise']['gates'])
                self.assertEqual(norm.outputs, case['normalise']['outputSignals'])
                # NCFF text identical, and it parses back to the same circuit
                text = ncff(norm, target)
                self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), case['ncff_sha256'])
                back = parse_ncff(text)
                self.assertEqual((back.gates, back.outputs), (norm.gates, norm.outputs))
                # the kernel's own (trimmed) circuit: same program as before, verifies the same
                vs = ValueSet(target.n_inputs, target.rows, circuit.masks())
                vs.trim()
                gates, outputs = vs.gates()
                kernel = {'gates': [list(g) for g in gates], 'outputSignals': list(outputs)}
                self.assertEqual(hashlib.sha256(json.dumps(kernel, sort_keys=True).encode())
                                 .hexdigest(), case['kernel_sha256'])
                v2 = self.compare(Circuit(vs.n, gates, outputs), target, case['kernel_verify'])
                self.assertEqual(v2.gate_count, vs.size())
                self.assertEqual(v.gate_count, case['verify']['gate_count'])
        seeds = sum(len(t.seeds) for t in map(load_target, catalog()))
        self.assertGreaterEqual(len(cases), seeds)
        self.assertGreaterEqual(len(cases), 10)

    def test_circuit_files(self):
        """Every XOR-only NIST-format circuit stored next to a map computes that map."""
        checked = 0
        for name in catalog():
            target = load_target(name)
            for path in sorted((CIRCUITS_DIR / name).glob('*.circ.txt')):
                text = path.read_text()
                try:
                    circuit = parse_ncff(text)
                except ValueError as exc:
                    if 'not an XOR-only' in str(exc):
                        continue
                    raise
                with self.subTest(file=str(path)):
                    v = verify(circuit, target)
                    self.assertTrue(v.equivalent, v.reason)
                    checked += 1
        if not checked:
            self.skipTest('no XOR-only .circ.txt files in circuits/ yet')


class VerifyFailureTest(unittest.TestCase):
    def setUp(self):
        # y0 = x0^x1, y1 = x0^x1^x2
        self.target = Target.make('tiny', 3, [0b011, 0b111])
        self.good = Circuit(3, [(0, 1), (3, 2)], [3, 4])

    def test_good(self):
        v = verify(self.good, self.target)
        self.assertTrue(v.ok)
        self.assertEqual((v.gate_count, v.live_gates, v.dead_gates, v.depth), (2, 2, 0, 2))
        self.assertIsNone(v.reason)

    def test_reasons(self):
        cases = [
            (Circuit(3, [(0, 1), (3, 5)], [3, 4]), 'non-topological'),
            (Circuit(3, [(0, 1), (3, 2)], [4, 3]), 'does not equal'),
            (Circuit(3, [(0, 1), (3, 2)], [3]), 'entries'),
            (Circuit(3, [(0, 1), (3, 2)], [3, 9]), 'out of range'),
            (Circuit(3, [(0, 1)], None), 'no signal'),
            (Circuit(4, [(0, 1), (4, 2)], [4, 5]), 'inputs'),
        ]
        for circuit, fragment in cases:
            v = verify(circuit, self.target)
            self.assertFalse(v.ok)
            self.assertFalse(v.equivalent)
            self.assertIn(fragment, v.reason)
        v = verify(self.good, self.target, cap=1)
        self.assertTrue(v.equivalent)
        self.assertFalse(v.within_cap)
        self.assertFalse(v.ok)
        self.assertIn('exceeds cap', v.reason)
        with self.assertRaises(ValueError):
            verify(self.good, self.target, cap=-1)
        bad_json = verify({'gates': 7, 'inputCount': 3}, self.target)
        self.assertFalse(bad_json.ok)

    def test_dead_gates_inferred_outputs_and_duplicates(self):
        # A dead gate, a duplicate mask (x0^x1 twice) and inferred outputs.
        c = Circuit(3, [(0, 1), (1, 2), (0, 1), (3, 2)])
        v = verify(c, self.target)
        self.assertTrue(v.ok)
        self.assertTrue(v.outputs_inferred)
        self.assertEqual(v.outputs, [3, 6])
        self.assertEqual((v.live_gates, v.dead_gates), (2, 2))
        self.assertIsNone(v.dag_sha256)            # duplicate masks: no DAG identity
        norm = normalise(c, self.target)
        self.assertEqual(norm.gates, [(0, 1), (3, 2)])
        self.assertEqual(norm.outputs, [3, 4])

    def test_shallowest_recipe(self):
        # x0^x1^x2^x3 built as a chain (depth 3) and as a tree (depth 2): keep the tree.
        target = Target.make('t4', 4, [0b1111])
        c = Circuit(4, [(0, 1), (4, 2), (5, 3), (2, 3), (4, 7)], [6])
        v = verify(c, target)
        self.assertEqual(v.depth, 3)
        norm = normalise(Circuit(4, c.gates), target)
        self.assertEqual(verify(norm, target).depth, 2)
        self.assertEqual(len(norm.gates), 3)

    def test_zero_and_unit_rows(self):
        target = Target.make('z', 3, [0, 0b100, 0b011, 0b011])
        c = Circuit(3, [(0, 1)], [-1, 2, 3, 3])
        v = verify(c, target)
        self.assertTrue(v.ok, v.reason)
        self.assertEqual(v.depth, 1)
        inferred = verify(Circuit(3, [(0, 1)]), target)
        self.assertEqual(inferred.outputs, [-1, 2, 3, 3])
        self.assertFalse(verify(Circuit(3, [(0, 1)], [-1, 2, 3, -1]), target).ok)
        with self.assertRaises(ValueError):
            ncff(c, target)
        self.assertEqual(normalise(c, target).outputs, [-1, 2, 3, 3])


class JsonTest(unittest.TestCase):
    def test_roundtrip_and_variants(self):
        target = load_target('joltik')
        circuit = target.seeds[0].load(target.n_inputs)
        data = circuit.to_json(target)
        self.assertEqual(data['gateCount'], 44)
        self.assertEqual(data['depth'], 7)
        self.assertEqual(data['benchmark'], 'joltik')
        back = Circuit.from_json(json.loads(json.dumps(data)))
        self.assertEqual((back.n_inputs, back.gates, back.outputs),
                         (circuit.n_inputs, circuit.gates, circuit.outputs))
        # outputs as a {"0": ...} map inside provenance, input count from the caller
        variant = {'gates': data['gates'],
                   'provenance': {'outputs': {str(i): x for i, x in enumerate(data['outputSignals'])}}}
        c2 = Circuit.from_json(variant, 16)
        self.assertEqual(c2.outputs, data['outputSignals'])
        self.assertEqual(Circuit.from_json({'gates': data['gates']}, 16).outputs, None)
        with self.assertRaises(ValueError):
            Circuit.from_json({'gates': data['gates']})
        with self.assertRaises(ValueError):
            Circuit.from_json({'gates': data['gates'], 'inputCount': 16}, 32)
        with self.assertRaises(ValueError):
            Circuit.from_json({'gates': [[1, 2, 3]], 'inputCount': 16})
        with self.assertRaises(ValueError):
            Circuit.from_json(dict(data, outputs=[0] * 16))     # conflicting output maps

    def test_dag_hash_from_matrix_hash_only(self):
        # Regression: with a matrix hash instead of a target, a circuit dict using
        # "input_count" raised KeyError and a gate list raised TypeError.
        target = load_target('joltik')
        circuit = target.seeds[0].load(target.n_inputs)
        want = dag_sha256(circuit, target)
        digest = target.matrix_sha256
        self.assertEqual(dag_sha256(circuit, digest), want)
        data = circuit.to_json(target)
        self.assertEqual(dag_sha256(data, digest), want)
        alt = {'gates': data['gates'], 'input_count': 16}
        self.assertEqual(dag_sha256(alt, digest), want)
        with self.assertRaises(ValueError):
            dag_sha256(list(circuit.gates), digest)

    def test_save_load(self):
        import tempfile
        target = load_target('fox-mu4')
        circuit = target.seeds[0].load(target.n_inputs)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'c.json')
            circuit.save(path, target, note='x')
            loaded = Circuit.load(path)
            self.assertEqual(loaded.gates, circuit.gates)
            self.assertEqual(loaded.meta['note'], 'x')
            npath = os.path.join(tmp, 'c.ncff')
            with open(npath, 'w') as fh:
                fh.write(ncff(circuit, target))
            self.assertEqual(Circuit.load(npath).gates, circuit.gates)


if __name__ == '__main__':
    unittest.main()
