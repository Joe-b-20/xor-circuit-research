"""Tests for ops/transport.py (forward <-> inverse AES S-box transport).

    python3 -m unittest discover -s search/nonlinear/boolflux/tests -t search/nonlinear
"""
import json
import os
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
sys.path.insert(0, str(PKG.parent))
sys.path.insert(0, str(PKG / 'ops'))

from boolflux import aesfn, aes_check   # noqa: E402
import transport as TP                  # noqa: E402
import common as CM                     # noqa: E402

SEEDS = PKG.parent / 'seeds'
FWD = SEEDS / 'aes-sbox' / 'aes-sbox-a32-ad4-g117-gd19-xx85-6.circ.txt'
INV = SEEDS / 'aes-invsbox' / 'aes-invsbox-a32-ad4-g117-gd21-xx85-10.circ.txt'


def tab(c):
    return tuple(c.value_table())


class TestTransportMaps(unittest.TestCase):
    def test_maps_identities(self):
        # maps() asserts dst = Out o src o In on all 256 values; a few symmetries in both directions
        for src in ('aes-sbox', 'aes-invsbox'):
            for lam, k in ((1, 0), (188, 0), (189, 0), (2, 1), (255, 7)):
                In, cin, Out, cout = TP.maps(src, lam, k)
                self.assertEqual(len(In), 8); self.assertEqual(len(Out), 8)

    def test_identity_constants(self):
        # S^-1 = Aff^-1 o F o Aff^-1: input constant Ainv(0x63) = 0x05, the same on the output side
        In, cin, Out, cout = TP.maps('aes-sbox', 1, 0)
        self.assertEqual((cin, cout), (0x05, 0x05))
        In, cin, Out, cout = TP.maps('aes-invsbox', 1, 0)
        self.assertEqual((cin, cout), (0x63, 0x63))


class TestTransportBuild(unittest.TestCase):
    def setUp(self):
        self.f = CM.load(FWD); self.i = CM.load(INV)

    def check_all(self, src, c, dst_c):
        self.assertEqual(tab(dst_c), aesfn.table(TP.OTHER[src]))
        self.assertEqual(CM.metrics(dst_c)[:2], CM.metrics(c)[:2])          # same A and AD

    def test_wraps_compute_the_other_function(self):
        for src, c in (('aes-sbox', self.f), ('aes-invsbox', self.i)):
            for lam, k in ((1, 0), (188, 0), (7, 3)):
                In, cin, Out, cout = TP.maps(src, lam, k)
                self.check_all(src, c, TP.wrap(c, In, cin, Out, cout))
                self.check_all(src, c, TP.wrap_slp(c, In, cin, Out, cout, random.Random(1), 2))
                fl = TP.flat_bottom(TP.flat_top(c, In, cin), Out, cout)
                self.check_all(src, c, fl)

    def test_flat_is_identity_on_function_and_depth_optimal_top(self):
        c = self.f
        fl = TP.flat_top(c)
        self.assertEqual(tab(fl), tab(c))
        self.assertLessEqual(CM.metrics(fl)[3], CM.metrics(c)[3])            # balanced trees never deeper
        fb = TP.flat_bottom(c)
        self.assertEqual(tab(fb), tab(c))
        self.assertLessEqual(CM.metrics(fb)[3], CM.metrics(c)[3])

    def test_round_trip(self):
        In, cin, Out, cout = TP.maps('aes-sbox', 1, 0)
        inv = TP.wrap_slp(self.f, In, cin, Out, cout, random.Random(2), 2)
        In2, cin2, Out2, cout2 = TP.maps('aes-invsbox', 1, 0)
        back = TP.wrap(inv, In2, cin2, Out2, cout2)
        self.assertEqual(tab(back), aesfn.table('aes-sbox'))
        self.assertEqual(CM.metrics(back)[:2], CM.metrics(self.f)[:2])

    def test_depth_build_meets_cap(self):
        aesfn.use('aes-invsbox')
        try:
            In, cin, Out, cout = TP.maps('aes-sbox', 1, 0)
            for dD in (0, 2):
                c, info = TP.build(self.f, In, cin, Out, cout, CM.metrics(self.f)[3] + dD, 2, 1, random.Random(3))
                self.check_all('aes-sbox', self.f, c)
                self.assertLessEqual(CM.metrics(c)[3], info['cap_used'])
                self.assertGreaterEqual(info['cap_used'], info['flat'][3])
        finally:
            aesfn.use('aes-sbox')


class TestTransportSelection(unittest.TestCase):
    def test_pull_schedule_start_relative_caps(self):
        self.assertEqual(TP.pull_schedule('g:+0:120,m:s+2:150,m:s:200,m:s-1:10:rk0,o:19:5', 22),
                         'g:+0:120,m:24:150,m:22:200,m:21:10:rk0,o:19:5')

    def test_depth_screen_picks_lowest_flat_gd(self):
        aesfn.use('aes-invsbox')
        try:
            c = CM.load(FWD)

            class A:
                screen_runs = 1; seed = 1
            a = A()
            items = TP.map_list('id,depth:2', c, 'aes-sbox', a, lambda *x: None)
            self.assertEqual(items[0][:2], (1, 0))
            self.assertEqual(len(items), 3)
            ds = a._depth_screen
            self.assertEqual(sum(ds['gd_histogram'].values()), 2040)
            gmin = min(ds['gd_histogram'])
            for lam, k, label in items[1:]:
                In, cin, Out, cout = TP.maps('aes-sbox', lam, k)
                fl = TP.flat_bottom(TP.flat_top(c, In, cin), Out, cout)
                self.assertEqual(CM.metrics(fl)[3], gmin)
                self.assertEqual(tab(fl), aesfn.table('aes-invsbox'))
        finally:
            aesfn.use('aes-sbox')


class TestTransportOperator(unittest.TestCase):
    def test_operator_no_pull(self):
        # forward NIST circuit -> verified inverse circuits with sidecars and a run record
        with tempfile.TemporaryDirectory() as d:
            env = dict(os.environ, BOOLFLUX_FUNCTION='aes-sbox', BOOLFLUX_CACHE=str(Path(d) / 'cache'))
            env.pop('BOOLFLUX_LINEAGE', None)
            out = Path(d) / 'out'
            r = subprocess.run([sys.executable, str(PKG / 'ops' / 'transport.py'), '--in', str(FWD), '--target', str(FWD),
                                '--seconds', '120', '--out', str(out), '--maps', 'id', '--ladder', '0',
                                '--synth-seeds', '1', '--bp-runs', '1', '--pull', ''],
                               capture_output=True, text=True, env=env, timeout=600)
            self.assertEqual(r.returncode, 0, r.stderr[-2000:])
            res = json.loads((out / 'result.json').read_text())
            self.assertEqual(res['status'], 'ok')
            self.assertEqual(len(res['builds']), 2)                          # slp variant + one cap
            self.assertTrue((out / 'run.json').exists())
            circs = sorted(out.glob('transport-*.circ.txt'))
            self.assertTrue(circs)
            for p in circs:
                v = aes_check.check(str(p), 'aes-invsbox')
                self.assertTrue(v['ok'], v)
                self.assertEqual(tuple(v['tuple'][:2]), (32, 4))
                side = json.loads(p.with_suffix('').with_suffix('.json').read_text())
                self.assertEqual(side['function'], 'aes-invsbox')
                self.assertIn('transport', side['how'])

    def test_refuses_same_function(self):
        with tempfile.TemporaryDirectory() as d:
            r = subprocess.run([sys.executable, str(PKG / 'ops' / 'transport.py'), '--in', str(FWD), '--target', str(FWD),
                                '--seconds', '10', '--out', d, '--function', 'aes-sbox', '--pull', ''],
                               capture_output=True, text=True, timeout=120)
            self.assertNotEqual(r.returncode, 0)


if __name__ == '__main__':
    unittest.main()
