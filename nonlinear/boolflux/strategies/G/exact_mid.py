"""Exact test (track G): is a given 5-dim space S of functions of N (mod affine) exactly the product
span of a 5-AND circuit on the 4 bits of N?

If 5 products p_1..p_5 (each an AND of two affine combinations of 1, N-bits and earlier products)
must have S inside span(1, N, p_1..p_5), then (dim S = 5) their span mod affine IS S, so every p_i
lies in S + affine and the p_i are independent mod affine.  Depth-first search over all products
with that property (operand pairs = 2-dim subspaces of the current operand space mod constants):
complete, exact.  Also: the set of all 5-dim spaces span(n) + <v> realised by 5-AND circuits
(all 127 classes v mod span(1, N, n) tested).

usage: python3 exact_mid.py classes OUT.json           (all v)
       python3 exact_mid.py prob PROB.prob             (targets of an inv_fit/midfit problem, both groups)
"""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent / 'C'))

ONES = 0xFFFF
INP = [sum(1 << x for x in range(16) if (x >> (3 - i)) & 1) for i in range(4)]


class Sp:
    def __init__(self, vecs=()):
        self.rows = {}
        for v in vecs: self.add(v)

    def red(self, v):
        for p in sorted(self.rows, reverse=True):
            if (v >> p) & 1: v ^= self.rows[p]
        return v

    def add(self, v):
        v = self.red(v)
        if v: self.rows[v.bit_length() - 1] = v; return True
        return False

    def has(self, v):
        return self.red(v) == 0

    def copy(self):
        s = Sp(); s.rows = dict(self.rows); return s


def search(S, m=5, want_all=False):
    """S: list of 16-bit tables (dim m mod affine). Returns list of circuits (operand table pairs)."""
    aff = [ONES] + INP
    allowed = Sp(aff + list(S))           # S + affine
    assert len(allowed.rows) == 5 + m, 'S must have dim m mod affine'
    found = []

    def rec(ops, prods, spanP):
        if len(prods) == m:
            found.append(list(prods)); return not want_all
        # operand space: span(1, N, products) ; enumerate 2-dim subspaces mod constants
        basis = INP + [p for _, _, p in prods]
        d = len(basis)
        vecs = []
        for c in range(1, 1 << d):
            t = 0
            for i in range(d):
                if (c >> i) & 1: t ^= basis[i]
            vecs.append((c, t))
        for i in range(len(vecs)):
            ca, a = vecs[i]
            for j in range(i + 1, len(vecs)):
                cb, b = vecs[j]
                if (ca ^ cb) < cb: continue          # one representative per 2-dim subspace
                p = a & b
                if not allowed.has(p): continue
                if spanP.has(p): continue            # must be new mod affine + earlier products
                sp2 = spanP.copy(); sp2.add(p)
                # last product used only if it is the newest? (no ordering restriction: complete)
                if rec(ops, prods + [(a, b, p)], sp2): return True
        return False

    rec(None, [], Sp(aff))
    return found


def n16():
    from ll_prob import ninv_coords
    import inv_fit as IF
    idx, _ = IF.coord_index()
    return [IF.to16(t, idx) for t in ninv_coords()]


def main():
    if sys.argv[1] == 'classes':
        n = n16()
        base = Sp([ONES] + INP + n)
        assert len(base.rows) == 9
        # all classes v mod base: enumerate v over a complement basis
        comp = []
        sp = base.copy()
        for x in range(1 << 16):
            if sp.add(x): comp.append(x)
            if len(comp) == 7: break
        res = {}
        for c in range(1, 128):
            v = 0
            for i in range(7):
                if (c >> i) & 1: v ^= comp[i]
            f = search(n + [v])
            res['%04x' % base.red(v)] = len(f) > 0
        ok = [k for k, b in res.items() if b]
        Path(sys.argv[2]).write_text(json.dumps({'achievable': ok, 'n_classes': 127}, indent=1))
        print(json.dumps({'achievable_classes': len(ok), 'of': 127}))
    elif sys.argv[1] == 'prob':
        from sat_small import read_prob
        npts, free, K, groups = read_prob(sys.argv[2])
        T = [t for g in groups for t in g[0]]
        add = [t for g in groups for t in g[1]]
        S = Sp([ONES] + INP + add)
        Sb = [t for t in T if S.add(t)]
        print(json.dumps({'dim_targets_beyond_affine_addends': len(Sb)}))
        if len(Sb) == 5:
            f = search(Sb)
            print(json.dumps({'exists': len(f) > 0}))


if __name__ == '__main__':
    main()
