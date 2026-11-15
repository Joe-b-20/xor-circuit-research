#!/usr/bin/env python3
"""T3: level-3 GF(4)-coordinate freedom of the AD3 circuits.

Reading ([C] checked on the circuit by gf4check.py): level 3 = 12 products Q_w * R_c with
Q_w = Tr(w x^170) (3 functions, x^170 = Delta^-1 in GF(4)) and R_c = Tr(c x^84), all Tr(c x^84) in S.
A product set {(w_a, c) : c in basis of C_a}, a = 1..3, gives the outputs iff U = {(z, rho z)} lies in
C1 x 0 + 0 x C2 + diag(C3) (see NOTES); 12 products are the minimum for this product form [C].
Here we (1) price every R_c by its XOR distance from the circuit's signals of AND level <= 1 plus the
level-2 ANDs (region-2 XORs are rebuilt), (2) enumerate admissible (C1, C2, C3), (3) for each pick the
cheapest basis per class (matroid greedy = optimal for the additive price), (4) check the outputs are
in the span of the 12 products, and report the cheapest choices.
    python3 gf4basis.py CIRCUIT [--top 20]
"""
import argparse
import itertools
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux.hub.common import load, metrics, _gpow, _gmul, ONES   # noqa: E402
from pairs import and_levels, Basis                                 # noqa: E402


def trace(z):
    t = 0; y = z
    for _ in range(8):
        t ^= y; y = _gmul(y, y)
    return t


def table(f):
    v = 0
    for x in range(256):
        if f(x) & 1: v |= 1 << x
    return v


P170 = [_gpow(x, 170) for x in range(256)]
P84 = [_gpow(x, 84) for x in range(256)]
RT = {cc: table(lambda x, cc=cc: trace(_gmul(cc, P84[x]))) for cc in range(1, 256)}
QT = {w: table(lambda x, w=w: trace(_gmul(w, P170[x]))) for w in range(1, 256)}


def dists(base, targets, maxd=3):
    """XOR distance (number of 2-input XOR/XNOR gates) of each target from the base set, up to complement"""
    B = set()
    for b in base: B.add(b); B.add(b ^ ONES)
    bl = list({min(b, b ^ ONES) for b in base})
    P = set()
    for u, v in itertools.combinations(bl, 2):
        w = u ^ v; P.add(w); P.add(w ^ ONES)
    out = {}
    for k, t in targets.items():
        if t in B: out[k] = 0
        elif t in P: out[k] = 1
        elif any((t ^ b) in P for b in bl): out[k] = 2
        elif maxd >= 3 and any((t ^ p) in P for p in P): out[k] = 3
        else: out[k] = 4
    return out


def span_elems(basis):
    els = [0]
    for b in basis: els += [e ^ b for e in els]
    return els[1:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('circuit'); ap.add_argument('--top', type=int, default=20)
    args = ap.parse_args()
    c = load(args.circuit); n = c.n; t = c.tables(); al = and_levels(c); NS = n + len(c.gates)
    m0 = metrics(c)
    base = [t[s] for s in range(NS) if al[s] <= 1] + [t[g] for g in range(n, NS) if c.gates[g - n][0] == 8 and al[g] == 2]
    d = dists(base, RT)
    from collections import Counter
    print(m0, 'R_c price histogram (c=1..255):', sorted(Counter(d.values()).items()))
    # classes of the current circuit
    cur = {}
    inv = {v: k for k, v in RT.items()}; invq = {}
    for w, v in QT.items(): invq.setdefault(v, w); invq.setdefault(v ^ ONES, w)
    for g in range(n, NS):
        op, a, b = c.gates[g - n]
        if op != 8 or al[g] != 3: continue
        qa = [s for s in (a, b) if t[s] in invq]; ra = [s for s in (a, b) if t[s] in inv or t[s] ^ ONES in inv]
        if not qa or not ra: print('unexpected product s%d' % g); return
        wq = t[qa[0]]
        wq = min(wq, wq ^ ONES)
        rv = t[ra[0]]; cc = inv.get(rv) or inv.get(rv ^ ONES)
        cur.setdefault(wq, []).append(cc)
    qkeys = sorted(cur)
    print('current classes:', [(invq[q], cur[q], [d[x] for x in cur[q]]) for q in qkeys])
    # Q identity per class: which GF(4)* element; the 3 Q functions
    # admissible triples: test via the output span directly
    outs = [t[s] for s in c.outputs]

    def ok(choice):
        prods = []
        for q, cs in zip(qkeys, choice):
            qt = q if q & 1 == 0 else q   # function itself
            for cc in cs: prods.append(qt & RT[cc])
        Bs = Basis([ONES] + prods)
        return all(Bs.reduce(o) == 0 for o in outs)

    print('current choice admissible:', ok([cur[q] for q in qkeys]))
    # structure: C_a as GF(2)-span; is C_b = lambda * C_a for some lambda?
    spans = [set(span_elems(cur[q])) for q in qkeys]
    for i, j in ((0, 1), (1, 2), (0, 2)):
        lam = [l for l in range(1, 256) if {_gmul(l, z) for z in spans[i]} == spans[j]]
        print('C%d -> C%d scalars:' % (i, j), lam)
    np = sum(1 for _ in range(1))
    return d, cur, qkeys, spans


if __name__ == '__main__':
    main()
