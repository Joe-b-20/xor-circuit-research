"""BoolFlux's two verifiers over every Boolean circuit of the repository (circuits/<folder>/ without a
*.mat.txt; files in logs/ are records and are skipped).  circuits/check.py checks the same files with
a third implementation (circuits/boolcirc).

    python3 -m unittest discover -s search/nonlinear/boolflux/tests -t search/nonlinear

Function of a file: a *.fn.json in its folder ({"name", "n_inputs", "n_outputs", "table"}; if there
are several, the one whose name starts the file name), else the AES S-box, inverse S-box or the two with a
direction bit by name (aes-sbox..., aes-invsbox..., aes-sbox-sel...).  Both sides read the file with their own parser and evaluate every
input in NIST's bit order (input i and output i are bit 7-i, 'msb/msb'); their metrics must agree.
"""
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
REPO = PKG.parents[2]
sys.path.insert(0, str(PKG.parent)); sys.path.insert(0, str(PKG / 'independent'))

from boolflux import core, targets   # noqa: E402
import verify as V                   # noqa: E402

CIRCUITS = REPO / 'circuits'


def boolean_files():
    out = []
    for d in sorted(p for p in CIRCUITS.iterdir() if p.is_dir() and p.name != 'boolcirc'):
        if any(d.glob('*.mat.txt')):
            continue                                   # a linear map
        out += sorted(f for f in d.rglob('*.circ.txt') if 'logs' not in f.relative_to(d).parts[:-1])
    return out


def function_of(path):
    """(n, m, table) or None."""
    tables = sorted(path.parent.glob('*.fn.json'))
    if len(tables) > 1:
        tables = [t for t in tables if path.name.startswith(t.name[:-len('.fn.json')])]
    if len(tables) == 1:
        d = json.loads(tables[0].read_text())
        return d['n_inputs'], d['n_outputs'], list(d['table'])
    name = path.name.lower()
    if name.startswith('aes-sbox-sel'):                # NIST's aes-sbox-sel: c x0..x7, S-box for c = 0, inverse for c = 1
        return 9, 8, V.aes_sbox() + V.aes_inv_sbox()
    if name.startswith(('aes-invsbox', 'aes-sbox-inv', 'aes-sbox-rev')):
        return 8, 8, V.aes_inv_sbox()
    if name.startswith('aes-sbox'):
        return 8, 8, V.aes_sbox()
    return None


class TestRepositoryCircuits(unittest.TestCase):
    def test_tables_agree(self):
        """The independent verifier's AES tables equal targets.py's (the two sides do not share code)."""
        self.assertEqual(V.aes_sbox(), list(targets.aes_sbox()))
        self.assertEqual(V.aes_inv_sbox(), list(targets.aes_inv_sbox()))

    def test_every_boolean_circuit_verifies_twice(self):
        files = boolean_files()
        if not files:
            self.skipTest('no Boolean circuit folders in circuits/ yet')
        for f in files:
            with self.subTest(file=str(f.relative_to(REPO))):
                fn = function_of(f)
                self.assertIsNotNone(fn, 'no function known (name or *.fn.json)')
                n, m, table = fn
                c = core.read_ncff(str(f))
                self.assertEqual((c.n, c.m), (n, m))
                self.assertEqual(list(c.value_table()), table, 'boolflux.core: wrong function')
                r = V.verify_file(str(f), (n, m, table))
                self.assertTrue(r['ok'], r.get('errors'))
                cm, im = c.metrics(), r['metrics']
                self.assertEqual([cm[k] for k in ('A', 'AD', 'G', 'GD')], [im[k] for k in ('A', 'AD', 'G', 'GD')],
                                 'metrics differ between the two verifiers')


if __name__ == '__main__':
    unittest.main()
