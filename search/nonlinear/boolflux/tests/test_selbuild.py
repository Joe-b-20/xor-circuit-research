"""Tests for ops/selbuild.py (aes-sbox-sel from one S-box or inverse S-box circuit) and the aes-sbox-sel target.

    python3 -m unittest discover -s search/nonlinear/boolflux/tests -t search/nonlinear -p 'test_selbuild.py'
"""
import importlib.util
import json
import random
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
sys.path.insert(0, str(PKG.parent))
sys.path.insert(0, str(PKG / 'ops'))

from boolflux import core, targets      # noqa: E402
HAVE_DEPS = all(importlib.util.find_spec(m) is not None for m in ('numpy', 'pysat'))
SB = None
if HAVE_DEPS:
    import selbuild as SB                # noqa: E402   (numpy; its Boyar-Peralta rebuilds also python-sat)

SEEDS = PKG.parent / 'seeds'
FWD = SEEDS / 'aes-sbox' / 'aes-sbox-a32-ad4-g117-gd19-xx85-6.circ.txt'
INV = SEEDS / 'aes-invsbox' / 'aes-invsbox-a32-ad4-g117-gd21-xx85-10.circ.txt'


class TestSelTarget(unittest.TestCase):
    def test_target_matches_nist_file(self):
        """standard library only: the aes-sbox-sel target is NIST's table (S-box for c = 0, inverse for c = 1)"""
        n, m, t, _ = targets.load('aes-sbox-sel')
        fj = json.loads((SEEDS / 'aes-sbox-sel' / 'aes-sbox-sel.fn.json').read_text())
        self.assertEqual((n, m, t), (fj['n_inputs'], fj['n_outputs'], fj['table']))


@unittest.skipUnless(HAVE_DEPS, 'ops/selbuild.py needs numpy and python-sat')
class TestSel(unittest.TestCase):
    def test_target_is_nist_table(self):
        n, m, t, _ = targets.load('aes-sbox-sel')
        fj = json.loads((SEEDS / 'aes-sbox-sel' / 'aes-sbox-sel.fn.json').read_text())
        self.assertEqual((n, m), (fj['n_inputs'], fj['n_outputs']))
        self.assertEqual(t, fj['table'])
        self.assertEqual(SB.sel_table(), t)

    def test_min_mux_rank(self):
        for src, best in (('aes-sbox', {(31, 0), (95, 0), (174, 0)}), ('aes-invsbox', {(23, 0), (178, 0), (210, 0)})):
            r = {(l, k): sum(SB.Plan(src, l, k).r) for l in range(1, 256) for k in range(8)}
            self.assertEqual(min(r.values()), 8)
            self.assertEqual({lk for lk, v in r.items() if v == 8}, best)

    def test_builds(self):
        want = SB.sel_table()
        for path, lk in ((FWD, (31, 0)), (INV, (23, 0))):
            F = core.read_ncff(str(path)); A0 = F.metrics()['A']; AD0 = F.metrics()['AD']
            P = SB.Plan('aes-sbox' if path is FWD else 'aes-invsbox', *lk)
            bi = next(SB.bases(P.Din)); bo = next(SB.bases(P.Dout))
            for top, bottom in (('bp', 'wrap'), ('wrap', 'wrap'), ('flat', 'flat'), ('xdelta', 'leafg')):
                c = SB.build(F, P, bi, bo, random.Random(1), 1, top, bottom)
                m = c.metrics()
                self.assertEqual(list(c.value_table()), want, (path.name, top, bottom))
                self.assertEqual((m['A'], m['AD']), (A0 + 8, AD0 + 2), (path.name, top, bottom))

    def test_cli_records(self):
        """the command line writes run.json + events (runlog), a record beside every circuit, and checks every
        circuit with both verifiers"""
        import gzip
        import subprocess
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            r = subprocess.run([sys.executable, str(PKG / 'ops' / 'selbuild.py'), '--in', str(FWD), '--maps', '31:0',
                                '--top', '1', '--runs', '1', '--seed', '3', '--out', d], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr[-2000:])
            out = Path(d)
            run = json.loads((out / 'run.json').read_text())
            self.assertEqual((run['kind'], run['status'], run['function']), ('ops.selbuild', 'ok', 'aes-sbox-sel'))
            self.assertEqual(run['seeds'], {'seed': 3})
            self.assertEqual(run['starts'][0]['metrics'], [32, 4, 117, 19])
            self.assertTrue(run['sources_sha256'])
            res = json.loads((out / 'result.json').read_text())
            self.assertEqual(res['status'], 'ok')
            circs = sorted(out.glob('aes-sbox-sel-*.circ.txt'))
            self.assertEqual(len(circs), len(res['written']))
            self.assertTrue(circs)
            want = SB.sel_table()
            for p in circs:
                side = json.loads(p.with_name(p.name[:-len('.circ.txt')] + '.json').read_text())
                self.assertEqual(side['circuit_sha256'], SB.runlog.sha256_file(p))
                self.assertIn('independent', side['checks'])
                self.assertEqual(list(core.read_ncff(str(p)).value_table()), want)
                self.assertTrue(SB.IV.verify_file(str(p), SB.independent_fn())['ok'])
            evs = [json.loads(l) for l in gzip.decompress((out / 'events.jsonl.gz').read_bytes()).decode().splitlines()]
            self.assertEqual(sum(e['ev'] == 'improvement' for e in evs), len(circs))
            self.assertEqual(sum(e['ev'] == 'build' for e in evs), len(res['results']))


if __name__ == '__main__':
    unittest.main()
