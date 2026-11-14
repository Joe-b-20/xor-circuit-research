"""Build an AND/XOR circuit from a three-stage design and write NCFF:
  level-1 products (pairs of x-linear forms), the 5 inversion ANDs of the AD5 file (operands
  re-expressed over the available signals), last-layer GF(4)-norm members (A, s) with
  w = n + gamma N, outputs = S-box bits expressed over all signals.
Every operand / output is found by exact GF(2) linear algebra on 256-point truth tables and
realised by an XOR chain (XOR count is not optimised here; use the gate kernel with --cap-a).

usage: python3 build27.py --design FILE.json --out CIRC.txt
  design JSON: {"l1": [[[8 bits], [8 bits]], ...], "members": [[A, s], ...], "gamma": 17}
  or --a28 (rebuild the AD5 file's structure: validation of the builder)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import gf                                    # noqa: E402
from core import Circuit, write_ncff         # noqa: E402
from structure import analyse                # noqa: E402
from fam_check import gp, tr_tab, trK, OMEGA  # noqa: E402
from targets import aes_sbox                 # noqa: E402

AD5 = '/home/joebachir20/xcr-boolflux/nonlinear/nist/aes-sbox/aes-sbox-a28-ad5-g124-gd27-xx96-26.circ.txt'


class Builder:
    def __init__(self):
        self.gates = []
        self.tabs = list(gf.X)          # signal tables (inputs first)
        self.span = gf.Span()
        for i, t in enumerate(gf.X): self.span.add(t, 1 << i)
        self.n_and = 0

    def sig(self, op, a, b):
        self.gates.append((op, a, b))
        ta, tb = self.tabs[a], self.tabs[b]
        t = {6: ta ^ tb, 8: ta & tb, 3: ta ^ gf.ONES}[op]
        self.tabs.append(t)
        return len(self.tabs) - 1

    def register(self, s):
        """make signal s available as a basis element for later expressions"""
        self.span.add(self.tabs[s], 1 << s)

    def express(self, t):
        """signal index equal to table t (XOR chain over registered signals, NOT if needed)"""
        neg = False
        r, tag = self.span.reduce(t, 0)
        if r:
            r2, tag2 = self.span.reduce(t ^ gf.ONES, 0)
            if r2: raise ValueError('table not in span')
            neg, tag = True, tag2
        idx = [i for i in range(tag.bit_length()) if (tag >> i) & 1]
        if not idx: raise ValueError('constant table')
        cur = idx[0]
        for i in idx[1:]: cur = self.sig(6, cur, i)
        if neg: cur = self.sig(3, cur, cur)
        return cur

    def AND(self, ta, tb):
        a = self.express(ta); b = self.express(tb)
        s = self.sig(8, a, b); self.n_and += 1
        self.register(s)
        return s


def lin_table(bits):
    t = 0
    for i, b in enumerate(bits):
        if b: t ^= gf.X[i]
    return t


def build(l1, members, gamma, inv_from=AD5):
    B = Builder()
    for la, lb in l1:
        B.AND(lin_table(la), lin_table(lb))
    c, ands, outs, tt = analyse(inv_from)
    top = max(A['level'] for A in ands)
    for A in ands:
        if 1 < A['level'] < top:
            B.AND(A['Ltab'], A['Rtab'])
    N = [gf.power(p, 17) for p in range(256)]
    n = [gf.INV[v] for v in N]
    g = gp(gamma) if gamma is not None else 0
    w = [n[p] ^ (gf.mul(g, N[p]) if g else 0) for p in range(256)]
    w2 = gf.mul(OMEGA, OMEGA)
    for A, s in members:
        lt = tr_tab(A) ^ trK(s, w)
        mt = tr_tab(gf.mul(OMEGA, A)) ^ trK(gf.mul(w2, s), w)
        B.AND(lt, mt)
    sb = aes_sbox()
    outs = [B.express(gf.bit_table(sb, 7 - j)) for j in range(8)]
    circ = Circuit(8, 8, B.gates, outs, 'aes-sbox-trackC',
                   ['U%d' % i for i in range(8)], ['S%d' % j for j in range(8)])
    return circ.live(), B.n_and


def a28_design():
    c, ands, outs, tt = analyse(AD5)
    top = max(A['level'] for A in ands)
    from exp_stage3 import coords
    l1 = []
    for A in ands:
        if A['level'] == 1:
            l1.append((coords([gf.ONES] + gf.X, A['Ltab'])[1:], coords([gf.ONES] + gf.X, A['Rtab'])[1:]))
    return l1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--design', default=None)
    ap.add_argument('--a28', action='store_true')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    if a.a28:
        import json as _j
        l1 = a28_design()
        S = _j.loads(open('/home/joebachir20/xs-campaigns/2026-11-13-aes/C/logs/kj_sets.jsonl').readline())['members']
        members = [(m[1], m[2]) for m in S]
        gamma = 17
    else:
        d = json.load(open(a.design))
        l1, members, gamma = d['l1'], [tuple(m) for m in d['members']], d.get('gamma', 17)
    circ, nand = build(l1, members, gamma)
    m = circ.metrics()
    txt = write_ncff(circ, comments=['track C three-stage build: %d level-1, 5 inversion, %d last-layer ANDs'
                                     % (len(l1), len(members))])
    Path(a.out).write_text(txt, encoding='utf-8')
    print(json.dumps({'out': a.out, 'A': m['A'], 'G': m['G'], 'AD': m['AD'], 'GD': m['GD']}))


if __name__ == '__main__':
    main()
