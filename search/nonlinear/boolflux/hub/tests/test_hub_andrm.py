"""Hub operator andrm (hub/ops/op_andrm.py, opt-in; idea 09's recommendation, 2026-11-17):
    python3 -m unittest boolflux.hub.tests.test_hub_andrm   (from search/nonlinear/)

A circuit with one AND split in two (AND(a, b) -> AND(a, b ^ d) ^ AND(a, d), same function, A + 1) is put in an
archive; the operator's window AND removal finds an A - 1 rebuild, polishes it at its own caps and pulls it to
the source's GD (the kernel is replaced by a stub that records its caps: no test starts a kernel).  The
scheduler runs andrm once per front tuple (level 5), never as a repeat.  Standard library only (no pysat).
"""
import importlib.util
import random
import sys
import tempfile
import types
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from boolflux import core                                              # noqa: E402
from boolflux.hub import ops as HO, scheduler as SCH                   # noqa: E402
from boolflux.hub.common import load, metrics                          # noqa: E402
from boolflux.hub.tests.test_hub_invariants import sched, OPEN, P117   # noqa: E402

SCH.kernel_bin = lambda d: None
AND, XOR = 8, 6


def tearDownModule():
    for f in OPEN:
        try: f.close()
        except Exception: pass


def op_module():
    spec = importlib.util.spec_from_file_location('op_andrm', str(SCH.SCRIPTS['andrm']))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def split_and(c):
    """the first AND(a, b) replaced by AND(a, b ^ d) ^ AND(a, d): same function, one AND more"""
    n = c.n
    j = next(j for j, g in enumerate(c.gates) if g[0] == AND)
    a, b = c.gates[j][1:]; d = next(i for i in range(n) if i not in (a, b))
    gates = []; remap = {}
    for i, (op, x, y) in enumerate(c.gates):
        x = remap.get(x, x); y = remap.get(y, y)
        if i == j:
            t1 = n + len(gates); gates.append((XOR, y, d))
            t2 = n + len(gates); gates.append((AND, x, t1))
            t3 = n + len(gates); gates.append((AND, x, d))
            remap[n + i] = n + len(gates); gates.append((XOR, t2, t3))
            continue
        remap[n + i] = n + len(gates); gates.append((op, x, y))
    return core.Circuit(n, c.m, gates, [remap.get(o, o) for o in c.outputs])


class TestAndrm(unittest.TestCase):
    def test_removal_polish_and_pull_to_the_source_gd(self):
        OA = op_module()
        c0 = load(P117); cs = split_and(c0)
        self.assertEqual(cs.output_tables(), c0.output_tables())
        A, AD, G, GD = metrics(cs); self.assertEqual(A, metrics(c0)[0] + 1)
        calls = []
        real = HO._kernel

        def stub(c, caps, objective, seed, seconds, out, archive_dir):
            calls.append(dict(caps)); return [c], {}
        HO._kernel = stub
        old = OA.ANDRM_HITS; OA.ANDRM_HITS = 1
        try:
            with tempfile.TemporaryDirectory() as d:
                s = sched(d, '--ops', 'andrm')
                st, r, g = s.ar.admit(cs); self.assertEqual(st, 'admitted')
                args = types.SimpleNamespace(inp=r['id'], seconds=120, objective='a,ad,cost,gd', seed=3, archive=d,
                                             bests=8, max_cands=40)
                cands, info = OA.op_andrm(s.ar, args, random.Random(5), Path(d) / 'job')
                self.assertTrue(info['hits'], info)
                hA, hAD, hG, hGD = info['hits'][0]
                self.assertLess(hA, A)
                self.assertEqual(calls[0], {'A': hA, 'AD': hAD, 'GD': hGD})            # polish at the hit's own caps
                if hGD > GD:
                    self.assertEqual(calls[1], {'A': hA, 'AD': hAD, 'GD': GD})         # pull to the source's GD
                    self.assertEqual(len(calls), 2)
                else:
                    self.assertEqual(len(calls), 1); self.assertNotIn('pull', info)
                self.assertTrue(cands)
                for x in cands:
                    self.assertEqual(x.output_tables(), c0.output_tables())
                    self.assertLess(metrics(x)[0], A)
                s._lockf.close()
        finally:
            HO._kernel = real; OA.ANDRM_HITS = old

    def test_no_window_no_candidates(self):
        OA = op_module()
        c = load(P117)
        with tempfile.TemporaryDirectory() as d:
            s = sched(d, '--ops', 'andrm'); st, r, g = s.ar.admit(c)
            args = types.SimpleNamespace(inp=r['id'], seconds=0.5, objective='a,ad,cost,gd', seed=1, archive=d,
                                         bests=8, max_cands=40)
            real = HO._kernel; HO._kernel = lambda *a: self.fail('kernel without a hit')
            old = OA.search; OA.search = lambda c, rng, secs, max_hits=None: ([], {'rank': 3})
            try:
                cands, info = OA.op_andrm(s.ar, args, random.Random(1), Path(d) / 'job')
            finally:
                HO._kernel = real; OA.search = old
            self.assertEqual(cands, []); self.assertIn('no window AND removal', info['skip'])
            self.assertFalse(HO.applicability(info)['applicable'])
            s._lockf.close()

    def test_scheduler_once_per_front_tuple(self):
        with tempfile.TemporaryDirectory() as d:
            s = sched(d, '--ops', 'polish,andrm', '--variants-first'); s.seed([str(P117)])   # repeats after level 5
            i = next(iter(s.ar.rec)); t = s.target_key(i)
            s.attempts[('polish', t)] = 1; s.sattempts[('polish', s.skey(i))] = 1
            self.assertEqual(s.priority_choice(set())[:3], ('andrm', i, 'other'))
            s.attempts[('andrm', t)] = 1
            for _ in range(5):                         # repeats: polish only, never andrm
                ch = s.priority_choice(set())
                self.assertEqual(ch[0], 'polish'); s.attempts[('polish', t)] += 1
            s._lockf.close()
        self.assertNotIn('andrm', SCH.parser().parse_args(['--dir', '.']).ops.split(','))    # opt-in


if __name__ == '__main__':
    unittest.main()
