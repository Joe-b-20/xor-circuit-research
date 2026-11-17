"""Window exact SAT resynthesis (ops/winsat.py, ops/winsat_lib.py; idea 09, 2026-11-17).

    python3 -m unittest boolflux.tests.test_winsat      (from search/nonlinear/)

The strong encoding (dead steps first, live steps used, no removable steps) must keep the answers of
R1's encoding: same SAT/UNSAT on small exact queries (full adder; random 3-4 input functions at the
optimum and one below it), and a redundant XOR detour injected into a published circuit is removed.
A short winsat run records only aes_check-verified circuits.
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
sys.path.insert(0, str(PKG.parent)); sys.path.insert(0, str(OPS))

from boolflux import core                    # noqa: E402
import winsat_lib as R                       # noqa: E402

FWD = REPO / 'circuits' / 'aes-sbox'


def exact(k, fns, r, amax, strong, budget=200000):
    P = 1 << k
    vin = [sum(((t >> b) & 1) << t for t in range(P)) for b in range(k)]
    m = len(fns)
    okp = [0] * (1 << m)
    for t in range(P):
        v = sum(((fns[h] >> t) & 1) << h for h in range(m))
        okp[v] |= 1 << t
    sy = R.Synth(k, P, vin, okp, [0] * k, [0] * k, [9] * m, [9] * m, r, amax, strong=strong)
    out = sy.run(budget); sy.close()
    if out[0] == 'sat':
        v = R.simulate(out[1], k, vin, (1 << P) - 1)
        assert [v[o] for o in out[2]] == fns
    return out[0]


class TestStrongEncoding(unittest.TestCase):
    def test_full_adder(self):
        k = 3; P = 8
        vin = [sum(((t >> b) & 1) << t for t in range(P)) for b in range(k)]
        sm = vin[0] ^ vin[1] ^ vin[2]; cy = (vin[0] & vin[1]) | (vin[0] & vin[2]) | (vin[1] & vin[2])
        for strong in (False, True):
            self.assertEqual(exact(3, [sm, cy], 4, 4, strong), 'unsat')
            self.assertEqual(exact(3, [sm, cy], 5, 1, strong), 'sat')

    def test_random_functions_agree(self):
        rng = random.Random(7)
        for trial in range(30):
            k = rng.choice([3, 4]); P = 1 << k
            m = 2 if k == 3 else 1
            fns = [rng.getrandbits(P) for _ in range(m)]
            # optimum by R1's encoding, then both encodings at the optimum and one below
            opt = None
            for r in range(1, 7):
                if exact(k, fns, r, r, False) == 'sat': opt = r; break
            if opt is None: continue
            self.assertEqual(exact(k, fns, opt, opt, True), 'sat', (k, fns, opt))
            if opt > 1: self.assertEqual(exact(k, fns, opt - 1, opt - 1, True), 'unsat', (k, fns, opt))

    def test_detour_removed(self):
        rng = random.Random(3)
        src = sorted(FWD.glob('aes-sbox-a32-ad4-*.circ.txt'))[0]
        c = core.read_ncff(str(src)); n = c.n
        G0 = len(c.gates)
        xs = [j for j, g in enumerate(c.gates) if g[0] == R.XOR and g[1] != g[2]]
        j = rng.choice(xs); op, a, b = c.gates[j]
        # s = a ^ b  ->  ((a ^ d) ^ b) ^ d with d an input: 2 extra gates before position j
        d = 0 if a != 0 and b != 0 else 1
        gates = []; remap = {}
        for i, g in enumerate(c.gates):
            if i == j:
                t1 = n + len(gates); gates.append((R.XOR, a, d))
                t2 = n + len(gates); gates.append((R.XOR, t1, b))
                remap[n + i] = n + len(gates); gates.append((R.XOR, t2, d))
                continue
            op_, x, y = g
            x = remap.get(x, x); y = remap.get(y, y)
            remap[n + i] = n + len(gates); gates.append((op_, x, y))
        cc = core.Circuit(n, c.m, gates, [remap.get(o, o) for o in c.outputs], c.name, c.in_names, c.out_names)
        self.assertEqual(cc.output_tables(), c.output_tables())
        net = R.Net(cc)
        W = {remap[n + j] - 2, remap[n + j] - 1, remap[n + j]}
        ins, outs = net.info(W)
        P, vin, okp, tg = R.relation(net, W, ins, outs)
        rq, ra = net.req_ex(W, net.GD, net.AD)
        sy = R.Synth(len(ins), P, vin, okp, [net.lv[i] for i in ins], [net.al[i] for i in ins],
                     [rq[o] for o in outs], [ra[o] for o in outs], 2, 0, strong=True)
        out = sy.run(20000); sy.close()
        self.assertEqual(out[0], 'sat')
        chain, om = R.prune(out[1], out[2], len(ins))
        nc = R.splice(cc, net, W, ins, outs, chain, om)
        self.assertEqual(nc.output_tables(), c.output_tables())
        self.assertLessEqual(len(nc.gates), G0)


class TestAndRemoval(unittest.TestCase):
    def test_split_and_restored(self):
        """AND(a, b) replaced by AND(a, b ^ d) ^ AND(a, d): mode andrm finds a window that removes an AND."""
        import winsat
        import winsat_andrm as M
        src = sorted(FWD.glob('aes-sbox-a32-ad4-*.circ.txt'))[0]
        c = core.read_ncff(str(src)); n = c.n
        j = next(j for j, g in enumerate(c.gates) if g[0] == R.AND)
        op, a, b = c.gates[j]; d = next(i for i in range(n) if i not in (a, b))
        gates = []; remap = {}
        for i, g in enumerate(c.gates):
            op_, x, y = g; x = remap.get(x, x); y = remap.get(y, y)
            if i == j:
                t1 = n + len(gates); gates.append((R.XOR, y, d))
                t2 = n + len(gates); gates.append((R.AND, x, t1))
                t3 = n + len(gates); gates.append((R.AND, x, d))
                remap[n + i] = n + len(gates); gates.append((R.XOR, t2, t3))
                continue
            remap[n + i] = n + len(gates); gates.append((op_, x, y))
        cc = core.Circuit(n, c.m, gates, [remap.get(o, o) for o in c.outputs], c.name, c.in_names, c.out_names)
        self.assertEqual(cc.output_tables(), c.output_tables())
        A0 = sum(1 for g in cc.gates if g[0] == R.AND)
        net = R.Net(cc); rng = random.Random(1); best = A0
        for _ in range(400):
            st, nc, det = winsat.andrm_window(cc, net, rng)
            if nc is not None:
                self.assertEqual(nc.output_tables(), c.output_tables())
                best = min(best, sum(1 for g in nc.gates if g[0] == R.AND))
                if best < A0: break
        self.assertLess(best, A0)


class TestWinsatRun(unittest.TestCase):
    def test_short_run(self):
        src = sorted(FWD.glob('aes-sbox-a32-ad4-*.circ.txt'))[0]
        with tempfile.TemporaryDirectory() as td:
            r = subprocess.run([sys.executable, str(OPS / 'winsat.py'), '--in', str(src), '--target', str(src),
                                '--seed', '1', '--seconds', '12', '--out', td, '--budget', '2000'],
                               capture_output=True, text=True, timeout=120)
            self.assertEqual(r.returncode, 0, r.stderr[-2000:])
            res = json.loads((Path(td) / 'result.json').read_text())
            self.assertEqual(res['status'], 'ok')
            self.assertGreater(res['winsat']['windows'], 0)
            for p in Path(td).glob('*.circ.txt'):
                side = json.loads(p.with_suffix('').with_suffix('.json').read_text())
                self.assertIn('OK', side['aes_check'])
            lines = (Path(td) / 'windows.jsonl').read_text().splitlines()
            self.assertTrue(all('status' in json.loads(x) for x in lines))


if __name__ == '__main__':
    unittest.main()
