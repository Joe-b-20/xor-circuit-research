"""Rebuild operators ops/rebase.py and ops/bottom.py and their libraries (phase 2, W4).

    python3 -m unittest boolflux.tests.test_rebuild_ops      (from search/nonlinear/)

Exact speedups must not change decisions: gbasis.analyse with its upper-bound prune returns the unpruned
best / best_kraft / best_combo whenever best <= ub; bopt.Model.cost equals the earlier implementation; the
GF(4) tables of rebase_lib/gf4fn.py are gf4_lib's for the forward S-box and give verified builds on the
inverse.  Short rebase / bottom runs complete, record aes_check-verified circuits and log the fields the
analyses read (gbasis diagnostics, bottom SA summary and build flags).
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
REPO = PKG.parents[2]
OPS = PKG / 'ops'
sys.path.insert(0, str(PKG.parent)); sys.path.insert(0, str(OPS)); sys.path.insert(0, str(OPS / 'rebase_lib'))
sys.path.insert(0, str(OPS / 'bottom_lib'))

from boolflux import aesfn                 # noqa: E402

FWD = REPO / 'circuits' / 'aes-sbox'
INV_SEEDS = PKG.parent / 'seeds' / 'aes-invsbox'
FWD_SEEDS = PKG.parent / 'seeds' / 'aes-sbox'
INV157 = INV_SEEDS / 'aes-invsbox-a35-ad3-g157-gd15-xx122-27.circ.txt'
FWD165 = FWD / 'aes-sbox-a35-ad3-g165-gd13-xx130-60.circ.txt'
FWD45 = FWD_SEEDS / 'aes-sbox-a45-ad4-g141-gd12-xx96-25.circ.txt'


def load(p):
    from rebuild_common import load as ld
    return ld(p)


def ops_bottom():
    """ops/bottom.py as a module (by path: conj_lib/bottom.py has the same module name)"""
    import importlib.util
    if 'w4_ops_bottom' not in sys.modules:
        spec = importlib.util.spec_from_file_location('w4_ops_bottom', OPS / 'bottom.py')
        m = importlib.util.module_from_spec(spec); sys.modules['w4_ops_bottom'] = m; spec.loader.exec_module(m)
    return sys.modules['w4_ops_bottom']


def use(p):
    aesfn.use(aesfn.resolve('auto', str(p)))


def run_op(script, args, timeout=400):
    out = Path(tempfile.mkdtemp(prefix='bft-rb-'))
    cache = Path(os.environ.get('BOOLFLUX_CACHE') or (Path(tempfile.gettempdir()) / 'bft-rb-cache'))
    env = dict(os.environ, BOOLFLUX_CACHE=str(cache)); env.pop('BOOLFLUX_LINEAGE', None); env.pop(aesfn.ENV, None)
    p = subprocess.run([sys.executable, str(OPS / script)] + [str(x) for x in args] + ['--out', str(out)],
                       capture_output=True, text=True, env=env, timeout=timeout, cwd=str(REPO))
    return p, out


def jload(path):
    with open(path) as f:
        return json.load(f)


def events(path):
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


class _Fn(unittest.TestCase):
    """restores the process function ($BOOLFLUX_FUNCTION, set by aesfn.use) after each test: later test modules
    in the same process assume the default"""
    def setUp(self):
        self._fn = os.environ.get(aesfn.ENV)

    def tearDown(self):
        if self._fn is None: os.environ.pop(aesfn.ENV, None)
        else: os.environ[aesfn.ENV] = self._fn


class TestGbasisPrune(_Fn):
    def test_prune_identical_when_best_within_ub(self):
        import gbasis as GB
        for f, caps in ((INV157, (13, 14)), (FWD165, (12, 13))):
            use(f); c = load(f)
            for cap in caps:
                r0 = GB.analyse(c, cap); r1 = GB.analyse(c, cap, ub=1.0)
                self.assertLessEqual(r0['best'], 1.0)
                for k in ('best', 'best_kraft', 'best_combo'):
                    self.assertEqual(r0[k], r1[k], (f.name, cap, k))
                self.assertTrue(r1['exact'])
                self.assertEqual([p['pareto'] for p in r0['_pc']], [p['pareto'] for p in r1['_pc']])
                self.assertIn('beam_ub', r1['diag']); self.assertIn('ub', r1['diag'])

    def test_value_only_bound_exact(self):
        """value_only (move scans, --descend): the bound itself is exact below ub, also when it is above 1"""
        import gbasis as GB
        for f, caps in ((INV157, (12, 13, 14)), (FWD165, (12, 13))):
            use(f); c = load(f)
            for cap in caps:
                r0 = GB.analyse(c, cap)
                for ub in (1.0, 1.75, 99.0):
                    r2 = GB.analyse(c, cap, ub=ub, value_only=True)
                    if r0['best'] <= ub: self.assertEqual(r2['best'], r0['best'], (f.name, cap, ub))
                    else: self.assertGreater(r2['best'], ub)

    def test_prune_above_ub_reports_above(self):
        import gbasis as GB
        use(INV157); c = load(INV157)
        r0 = GB.analyse(c, 12)                  # bound 1.75 at 12
        r1 = GB.analyse(c, 12, ub=1.0)
        self.assertGreater(r0['best'], 1.0); self.assertGreater(r1['best'], 1.0)
        self.assertFalse(r1['exact']); self.assertTrue(r1['diag']['above_ub'])
        # the reported combo is achievable: feasible_combos at its own value accepts it
        self.assertGreaterEqual(r1['best'], r0['best'])


class TestBoptCost(_Fn):
    def test_cost_equals_reference(self):
        BT = ops_bottom()
        use(FWD45); c = load(FWD45)
        st, why = BT.setup(c, 4, 12, 45)
        self.assertIsNotNone(st, why)
        M, B, opts, info = st
        rng = random.Random(5)
        for pw in (0.0, 3.0):
            M.pw = pw
            for _ in range(300):
                ch = [rng.choice(o) for o in opts]
                self.assertEqual(M.cost(ch), M.cost_reference(ch))
            if info['own']:
                self.assertEqual(M.cost(info['own']), M.cost_reference(info['own']))

    def test_anneal_same_with_reference_cost(self):
        BT = ops_bottom()
        import time
        use(FWD45); c = load(FWD45)
        M, B, opts, info = BT.setup(c, 4, 12, 45)[0]
        M.pw = 3.0
        a = BT.anneal(M, B, opts, random.Random(3), 600, 2.0, time.time() + 1e9, None)
        Mod = type(M); orig = Mod.cost
        try:
            Mod.cost = Mod.cost_reference
            b = BT.anneal(M, B, opts, random.Random(3), 600, 2.0, time.time() + 1e9, None)
        finally:
            Mod.cost = orig
        self.assertEqual(a, b)


class TestJunkAbsorb(_Fn):
    """bottom --junk absorb (idea 05): Y-form junk as bit 8 of affine x-forms"""
    def test_default_junk(self):
        """default --junk: absorb5 for the inverse S-box only; the forward S-box keeps terms"""
        BT = ops_bottom()
        self.assertEqual(BT.default_junk('aes-invsbox'), 'absorb5')
        self.assertEqual(BT.default_junk('aes-sbox'), 'terms')

    def test_forward_without_junk_unchanged(self):
        BT = ops_bottom()
        import time
        use(FWD45); c = load(FWD45)
        M0, B0, o0, i0 = BT.setup(c, 4, 12, 45, 'terms')[0]
        a = BT.anneal(M0, B0, o0, random.Random(4), 500, 2.0, time.time() + 1e9, None)
        M1, B1, o1, i1 = BT.setup(c, 4, 12, 45, 'absorb')[0]
        self.assertEqual((B0, o0, i0['own']), (B1, o1, i1['own']))
        b = BT.anneal(M1, B1, o1, random.Random(4), 500, 2.0, time.time() + 1e9, None)
        BT.BO.NCOL = 8
        self.assertEqual(a, b)

    def test_inverse_absorb_builds(self):
        BT = ops_bottom()
        import time
        inv45 = INV_SEEDS / 'aes-invsbox-a45-ad4-g141-gd12-xx96-25.circ.txt'
        use(inv45); c = load(inv45)
        try:
            M, B, opts, info = BT.setup(c, 4, 12, 45, 'absorb')[0]
            self.assertEqual([len(o) for o in opts], [141] * 8)         # terms mode: 13 for the outputs with level-10 junk
            self.assertTrue(info['own'] is not None)
            self.assertTrue(all(BT.BO.sum_t(S) == B[j] for j, S in enumerate(info['own'])))
            self.assertTrue(any(p[1] & BT.BO.ONE for S in info['own'] for p in S))
            for sd in (1, 2):
                cc, ch = BT.anneal(M, B, opts, random.Random(sd), 800, 2.0, time.time() + 1e9, None)
                plan = {'circuit': str(inv45), 'cap': 12, 'Lb': info['Lb'], 'cost': cc,
                        'choice': [[list(p) for p in S] for S in ch], 'C': info['C'], 'nat': BT.BO.NROW == 5}
                BT.BU.RNG = None
                nc = BT.clean(BT.BU.build(plan))
                self.assertTrue(BT.verify(nc)[0])
                m = BT.metrics(nc)
                self.assertEqual(m[0], info['nfront'] + cc[1])
                self.assertLessEqual(m[3], 12)
        finally:
            BT.BO.NCOL = 8

    def test_inverse_absorb5_gd11(self):
        """absorb5 also absorbs the x-form junk (complemented Y operands): the 45@12 front at GD 11 (terms / absorb:
        not applicable, every output's 4 level-9 products already fill its Kraft sum) builds 17 + 32 ANDs"""
        BT = ops_bottom()
        import time
        inv45 = INV_SEEDS / 'aes-invsbox-a45-ad4-g141-gd12-xx96-25.circ.txt'
        use(inv45); c = load(inv45)
        try:
            self.assertIsNone(BT.setup(c, 4, 11, 99, 'absorb')[0])
            M, B, opts, info = BT.setup(c, 4, 11, 99, 'absorb5')[0]
            self.assertEqual([len(o) for o in opts], [1] * 8)
            cc, ch = BT.anneal(M, B, opts, random.Random(1), 50, 2.0, time.time() + 1e9, None)
            plan = {'circuit': str(inv45), 'cap': 11, 'Lb': info['Lb'], 'cost': cc,
                    'choice': [[list(p) for p in S] for S in ch], 'C': info['C'], 'nat': BT.BO.NROW == 5}
            BT.BU.RNG = None
            nc = BT.clean(BT.BU.build(plan))
            self.assertTrue(BT.verify(nc)[0])
            m = BT.metrics(nc)
            self.assertEqual((m[0], m[1]), (49, 4)); self.assertLessEqual(m[3], 11)
        finally:
            BT.BO.NCOL = 8; BT.BO.NROW = 4


class TestGf4Port(_Fn):
    def test_forward_tables_and_inverse_build(self):
        import gf4fn
        import gf4basis
        RT, QT = gf4fn.tables('aes-sbox')
        self.assertEqual(RT, gf4basis.RT); self.assertEqual(QT, gf4basis.QT)
        use(INV157); gf4fn.install('aes-invsbox')
        try:
            import nbscan, gf4build, pairs
            from boolflux.hub.common import _gmul
            from rebuild_common import verify
            c = load(INV157)
            pts = nbscan.current_points(c)
            self.assertEqual(len(pts), 4)
            nc = gf4build.build(c, pts, keep2=True)              # same points: the circuit rebuilt
            self.assertTrue(verify(nc)[0])
            built = 0
            for p in range(1, 256):
                q = list(pts); q[0] = p
                Bs = pairs.Basis([])
                if not all(Bs.add(_gmul(s, x)) for x in q for s in (1, 188)): continue
                self.assertTrue(verify(gf4build.build(c, q, keep2=True))[0]); built += 1
                if built >= 3: break
            self.assertEqual(built, 3)
        finally:
            gf4fn.install('aes-sbox')


class TestShortRuns(_Fn):
    def test_rebase_inverse_cap13(self):
        p, out = run_op('rebase.py', ['--in', INV157, '--target', 'aes-invsbox-a35-ad3-g190-gd14-xx155-27.circ.txt',
                                      '--seed', 3, '--seconds', 75, '--cap', 13, '--builds', 4, '--top', 1,
                                      '--stages', 1, '--stage-seconds', 6])
        self.assertEqual(p.returncode, 0, p.stdout[-2000:] + p.stderr[-2000:])
        res = jload(out / 'result.json')
        self.assertEqual(res['status'], 'ok')
        ev = events(out / 'rebase.jsonl')
        b = [e for e in ev if e['event'] == 'builds']
        self.assertTrue(b)
        self.assertEqual(b[0]['analyse_diag']['ub'], 1.0); self.assertIn('beam_ub', b[0]['analyse_diag'])
        self.assertTrue(any(e['event'] == 'stage' and 'kernel_stats' in e for e in ev))
        recs = sorted(out.glob('rebase-a35-ad3-*-gd13-*.circ.txt'))
        self.assertTrue(recs)                       # build(s) at GD 13 recorded (inverse S-box)
        for f in recs:
            side = jload(str(f).replace('.circ.txt', '.json'))
            self.assertTrue(side['aes_check'].startswith('OK')); self.assertEqual(side['function'], 'aes-invsbox')

    def test_bottom_forward_45(self):
        p, out = run_op('bottom.py', ['--in', FWD45, '--target', FWD45.name, '--seed', 2, '--seconds', 70,
                                      '--iters', 1500, '--pw', '3', '--polish-seconds', 5])
        self.assertEqual(p.returncode, 0, p.stdout[-2000:] + p.stderr[-2000:])
        res = jload(out / 'result.json')
        self.assertEqual(res['status'], 'ok')
        ev = events(out / 'bottom.jsonl')
        b = [e for e in ev if e['event'] == 'build']
        self.assertTrue(b)
        for k in ('sa', 'sa_s', 'build_s', 'verify_s', 'plan_equals_own', 'build_equals_start', 'phases'):
            self.assertIn(k, b[0])
        self.assertIn('iters_run', b[0]['sa'])
        self.assertTrue(all(e['ok'] for e in b))
        self.assertTrue(any(e['event'] in ('polish', 'polish-skip') for e in ev), [e.get('build') for e in b])
        for f in out.glob('bottom-*.circ.txt'):
            side = jload(str(f).replace('.circ.txt', '.json'))
            self.assertTrue(side['aes_check'].startswith('OK'))


if __name__ == '__main__':
    unittest.main()
