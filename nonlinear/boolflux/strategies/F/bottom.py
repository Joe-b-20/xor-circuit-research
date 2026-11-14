#!/usr/bin/env python3
"""Bottom-layer (AND-level-4 products + output XORs) redesign as a bilinear decomposition
(track F).

In the BP-style circuits every output is an XOR of products AND(c(y), f(U)), with c a linear
combination of the inversion outputs y0..y3 and f an affine form of the S-box inputs U.  Writing
y-combos as 4-bit vectors a and forms as 9-bit vectors b (8 inputs + constant), output i is the
tensor T_i = sum_k a_k (x) b_k (a 4x9 GF(2) matrix).  Any set of products whose tensors span
T_i gives a correct output (equality of tensors implies equality of functions).

Search (simulated annealing) over the product pool P: each output takes, among all
representations of T_i in span(P) (enumerated over the null space), the one with the smallest
Kraft sum at the cap (product arrival = arrival(c) + 1, arrival(c) = 10 for y0..y3, y0^y2,
y1^y3 and 11 for the other combos in NIST 116, shifted by --yshift), ties by fewer terms.
Cost = |P| + w_x * sum_i (|S_i| - 1) + w_f * (forms not among the base circuit's signals);
infeasible outputs are penalised.

    python3 bottom.py BASE.circ.txt --cap 14 --iters 20000 --seed 1 [--yshift 0] [--out OUT.json]
"""
import argparse
import itertools
import json
import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2])); sys.path.insert(0, str(HERE))
from boolflux import core   # noqa: E402
from depth import analyse   # noqa: E402
from invspec import spec, project   # noqa: E402
from skelxf import gate_forms, bits   # noqa: E402

ONES = (1 << 256) - 1


def vec(a, b):
    """a: 4-bit y-combo, b: 9-bit form -> 36-bit tensor."""
    v = 0
    for j in range(4):
        if (a >> j) & 1: v ^= b << (9 * j)
    return v


def solve_basis(vectors):
    """Gaussian elimination: returns (pivot rows with combination masks)."""
    rows = []   # (vec, mask over input indices)
    for k, v in enumerate(vectors):
        m = 1 << k
        for rv, rm, p in rows:
            if (v >> p) & 1: v ^= rv; m ^= rm
        if v:
            p = v.bit_length() - 1
            # keep rows reduced on new pivot
            new = []
            for rv, rm, rp in rows:
                if (rv >> p) & 1: rv ^= v; rm ^= m
                new.append((rv, rm, rp))
            rows = new + [(v, m, p)]
    return rows


def extract(c):
    n = c.n
    lv, al, req, GD, D, region, fo = analyse(c, 99)
    tabs = c.tables()
    ins, outs, _, _ = spec(c)
    # y tables over all 256 inputs: y0..y3 as the projected basis
    ins = ins[:4]
    proj = project(ins, outs, tabs)
    Y = [0x74cc, 0x7a2a, 0xcf48, 0xa2f8]
    # full tables of y0..y3 from the inversion-output signals
    ytab = {}
    for s, t in zip(outs, proj): ytab[t] = tabs[s]
    if not all(y in ytab for y in Y):
        # derive missing ones as XORs of available outputs
        pass
    yfull = [ytab[y] for y in Y]
    def combo_of(t):
        for a in range(1, 16):
            v = 0
            for j in range(4):
                if (a >> j) & 1: v ^= yfull[j]
            if v == t: return a
        return None
    form = gate_forms(c)
    def lin_of(s):
        f = form[s]
        if any(p > n for p in bits(f)): return None
        b = 0
        for p in bits(f):
            if p == 0: b |= 1 << 8
            else: b |= 1 << (p - 1)
        return b
    prods = []    # (a, b, signal)
    for s in range(n, n + len(c.gates)):
        op, x, y = c.gates[s - n]
        if op == 8 and al[s] == 4:
            ax, ay = combo_of(tabs[x]), combo_of(tabs[y])
            bx, by = lin_of(x), lin_of(y)
            if ax and by is not None: prods.append((ax, by, s))
            elif ay and bx is not None: prods.append((ay, bx, s))
            else: raise ValueError('product %d not of the form y-combo x form' % s)
    # outputs as XOR of products (+ const): skeleton forms over AND basis
    sk_and_index = {}
    na = 0
    for j, (op, x, y) in enumerate(c.gates):
        if op == 8: sk_and_index[n + j] = na; na += 1
    T = []
    for o in c.outputs:
        f = form[o]
        v = 0
        for (a, b, s) in prods:
            if (f >> (1 + n + sk_and_index[s])) & 1: v ^= vec(a, b)
        # check no other terms
        other = [p for p in bits(f) if p > 0 and not any(p == 1 + n + sk_and_index[s] for a, b, s in prods)]
        if other: raise ValueError('output has non-product terms')
        T.append((v, f & 1))
    # verify the tensor identity numerically
    Utabs = core.input_tables(n)
    def ftab(b):
        t = ONES if (b >> 8) & 1 else 0
        for i in range(8):
            if (b >> i) & 1: t ^= Utabs[i]
        return t
    out_tabs = c.output_tables()
    for i, (v, cst) in enumerate(T):
        t = ONES if cst else 0
        for j in range(4):
            row = (v >> (9 * j)) & 0x1FF
            if row: t ^= yfull[j] & ftab(row)
        assert t == out_tabs[i], 'tensor identity fails for output %d' % i
    forms_have = set()
    for s in range(n, n + len(c.gates)):
        b = lin_of(s)
        if b is not None: forms_have.add(b & 0xFF)
    for i in range(8): forms_have.add(1 << i)
    return prods, T, yfull, forms_have, lv


class Bottom:
    def __init__(self, T, arrival_a, D, forms_have, wx=0.6, wf=1.5):
        self.T = T; self.arr = arrival_a; self.D = D; self.have = forms_have; self.wx = wx; self.wf = wf

    def kraft(self, terms):
        return sum(2.0 ** (self.arr[a] + 1 - self.D) for a, b in terms)

    def evaluate(self, P):
        vecs = [vec(x, y) for x, y in P]
        basis = {}          # pivot bit -> (vector, mask); fully reduced
        deps = []
        for k, v in enumerate(vecs):
            m = 1 << k; w = v
            for p, (bv, bm) in basis.items():
                if (w >> p) & 1: w ^= bv; m ^= bm
            if not w:
                deps.append(m); continue
            p = w.bit_length() - 1
            for q in list(basis):
                bv, bm = basis[q]
                if (bv >> p) & 1: basis[q] = (bv ^ w, bm ^ m)
            basis[p] = (w, m)
        total_terms = 0; worst = 0.0; sets = []
        nd = min(len(deps), 12)
        for v, cst in self.T:
            w = v; m = 0
            for p, (bv, bm) in basis.items():
                if (w >> p) & 1: w ^= bv; m ^= bm
            if w: return None
            best = None
            for z in range(1 << nd):
                mm = m
                for i in range(nd):
                    if (z >> i) & 1: mm ^= deps[i]
                terms = [P[k] for k in range(len(P)) if (mm >> k) & 1]
                key = (max(0.0, self.kraft(terms) - 1.0), len(terms))
                if best is None or key < best[0]: best = (key, terms)
            sets.append(best[1]); worst = worst + best[0][0]; total_terms += len(best[1]) - 1
        newf = len({y & 0xFF for x, y in P} - self.have)
        cost = len(P) + self.wx * total_terms + self.wf * newf
        return cost, worst, sets


def basis_reduce(basis):
    return basis


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('base'); ap.add_argument('--cap', type=int, default=14)
    ap.add_argument('--iters', type=int, default=20000); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--yshift', type=int, default=0); ap.add_argument('--out', default='')
    ap.add_argument('--wx', type=float, default=0.6); ap.add_argument('--wf', type=float, default=1.5)
    a = ap.parse_args()
    c = core.read_ncff(a.base)
    prods, T, yfull, have, lv = extract(c)
    # arrivals of y combos in the base (116: y0..y3, y0^y2, y1^y3 at 10; others at 11)
    fast = {1, 2, 4, 8, 1 | 4, 2 | 8}
    arr = {x: (10 if x in fast else 11) + a.yshift for x in range(1, 16)}
    B = Bottom(T, arr, a.cap, have, a.wx, a.wf)
    P = [(x, y) for x, y, s in prods]
    r0 = B.evaluate(P)
    print('base bottom: %d products, cost %.1f, worst Kraft excess %.3f, terms %s' % (len(P), r0[0], r0[1], [len(s) for s in r0[2]]))
    rng = random.Random(a.seed)
    cur = list(P); cr = r0
    score = lambda r: r[0] + 30 * r[1] if r else 1e9
    best = (score(cr), list(cur), cr)
    # candidate pool: every (combo, form) where the form is a row of some T_i restricted
    # to one y, or an existing form; plus random forms
    rowforms = set()
    for v, cst in T:
        for j in range(4):
            row = (v >> (9 * j)) & 0x1FF
            if row: rowforms.add(row)
    rowforms |= {b for x, b in P}
    rowforms = sorted(rowforms)
    for it in range(a.iters):
        T_ = 2.0 * (1 - it / a.iters) + 0.05
        new = list(cur)
        mv = rng.random()
        if mv < 0.4 or len(new) < 4:
            new.append((rng.randrange(1, 16), rng.choice(rowforms) if rng.random() < 0.8 else rng.randrange(1, 512)))
        elif mv < 0.75:
            new.pop(rng.randrange(len(new)))
        else:
            k = rng.randrange(len(new)); x, y = new[k]
            if rng.random() < 0.5: new[k] = (rng.randrange(1, 16), y)
            else: new[k] = (x, rng.choice(rowforms))
        if len(set(new)) != len(new): continue
        r = B.evaluate(new)
        if r is None: continue
        s, s0 = score(r), score(cr)
        if s <= s0 or rng.random() < math.exp(-(s - s0) / T_):
            cur, cr = new, r
            if s < best[0] - 1e-9:
                best = (s, list(new), r)
                print('it %d: %d products, cost %.1f, worst excess %.3f, terms %s' % (it, len(new), r[0], r[1], [len(x) for x in r[2]]), flush=True)
    s, P, r = best
    print('best: %d products cost %.1f worst %.3f terms %s' % (len(P), r[0], r[1], [len(x) for x in r[2]]))
    if a.out:
        Path(a.out).write_text(json.dumps({'products': P, 'outputs': [[list(t) for t in st] for st in r[2]],
                                           'consts': [cst for v, cst in T], 'cap': a.cap, 'yshift': a.yshift}) + '\n')


if __name__ == '__main__':
    main()
