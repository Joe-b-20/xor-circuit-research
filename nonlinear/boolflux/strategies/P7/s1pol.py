#!/usr/bin/env python3
"""P7: polarity-aware stage-1 choice for GD10 circuits of the NIST 59@10 shape.

For every N-coordinate f_k (operand of an AND-level-2 gate) enumerate all ways to write it as
c + sum of products (l+a)(m+b) of <= 2-variable operands with Kraft sum <= 1 at gate level 4
(GL1 product = x_i x_j with no constant, weight 1/8; any other product GL2, weight 1/4), with
the operand constants solved exactly (GF(2) system on the linear part).  Then choose one
decomposition per f_k minimising the top linear layer: the number of distinct operand gates
(mask, polarity), where a plain input costs 0, a complemented input (NOT) 1, a 2-variable form
(XOR or XNOR) 1, together with the bottom's x-forms (exact polarity, from the circuit).
Shared products between coordinates are counted once (AND saved).

    s1pol.py CIRCUIT
"""
import itertools, sys
from collections import defaultdict
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s1lib as L  # noqa: E402
import bsel  # noqa: E402


def linpart(t):
    A = L.anf(t)
    return sum(1 << i for i in range(8) if (A >> (1 << i)) & 1), A & 1


def solve_consts(prods, lam):
    """prods: list of (l, m, gl1flag). find (a_p, b_p) with sum(b_p l_p + a_p m_p) = lam.
    returns list of solutions (each a tuple of (a,b) pairs), at most 8."""
    vecs = []; idx = []
    for (l, m, g1) in prods:
        lam ^= l & m          # intrinsic linear part of l*m (x_i * x_i = x_i)
    for p, (l, m, g1) in enumerate(prods):
        if g1: continue
        vecs.append(l); idx.append((p, 'b'))   # b_p multiplies l
        vecs.append(m); idx.append((p, 'a'))
    nv = len(vecs)
    sols = []
    # brute force over the (small) number of unknowns: nv <= 12 -> 4096
    for bits in range(1 << nv):
        s = 0
        for k in range(nv):
            if (bits >> k) & 1: s ^= vecs[k]
        if s == lam:
            ab = [[0, 0] for _ in prods]
            for k in range(nv):
                if (bits >> k) & 1:
                    p, w = idx[k]
                    ab[p][0 if w == 'a' else 1] = 1
            sols.append(tuple(tuple(x) for x in ab))
            if len(sols) >= 16: break
    return sols


def main():
    c = L.load(sys.argv[1])
    T, lg, la, Ys, Ylev = bsel.front_info(c)
    U, C = bsel.decompose_outputs(c, T, Ys)
    bottom = set()
    for u in U:
        for w in u:
            if bin(w).count('1') > 1: bottom.add((w, 0))
    import s1search
    fs, _, _, _ = s1search.coords(c)
    forms = [m for m in range(1, 256) if bin(m).count('1') <= 2]
    P2 = []   # GL2-capable products (l, m) any <= 2-var forms, nonzero wedge
    for l, m in itertools.combinations(forms, 2):
        w = L.wedge(l, m)
        if w: P2.append((l, m, w))
    P1 = [(1 << i, 1 << j, L.wedge(1 << i, 1 << j)) for i in range(8) for j in range(i + 1, 8)]
    W2 = defaultdict(list)
    for i1 in range(len(P2)):
        for i2 in range(i1 + 1, len(P2)):
            W2[P2[i1][2] ^ P2[i2][2]].append((i1, i2))
    alldec = []
    for k, f in enumerate(fs):
        q = L.quad(f); lam, c0 = linpart(f)
        decs = []
        # shapes (n2, n1): 4 GL2; 3 GL2 + <= 2 GL1; 2 GL2 + <= 4 GL1
        for n1 in range(0, 5):
            for g1 in itertools.combinations(range(28), n1):
                q1 = q
                for i in g1: q1 ^= P1[i][2]
                n2max = 4 if n1 == 0 else 3 if n1 <= 2 else 2
                for n2 in range(1, n2max + 1):
                    if n2 + n1 < 4: continue
                    if n2 == 4 or n2 == 3:
                        pass
                    cand = []
                    if n2 == 2:
                        cand = W2.get(q1, [])
                        cand = [tuple(x) for x in cand]
                    elif n2 == 3:
                        for i1 in range(len(P2)):
                            for (i2, i3) in W2.get(q1 ^ P2[i1][2], ()):
                                if i2 > i1: cand.append((i1, i2, i3))
                    elif n2 == 4:
                        for i1 in range(len(P2)):
                            for i2 in range(i1 + 1, len(P2)):
                                for (i3, i4) in W2.get(q1 ^ P2[i1][2] ^ P2[i2][2], ()):
                                    if i3 > i2: cand.append((i1, i2, i3, i4))
                    elif n2 == 1:
                        cand = [(i,) for i in range(len(P2)) if P2[i][2] == q1]
                    for cd in cand:
                        prods = [(P2[i][0], P2[i][1], 0) for i in cd] + [(P1[i][0], P1[i][1], 1) for i in g1]
                        for sol in solve_consts(prods, lam):
                            decs.append(tuple(sorted((l, ab[0], m, ab[1], g) for (l, m, g), ab in zip(prods, sol))))
            if n1 >= 2 and len(decs) > 5000: break
        decs = sorted(set(decs))
        print('f%d: %d decompositions (Kraft <= 1 at GL4, constants solved)' % (k, len(decs)), flush=True)
        alldec.append(decs)

    import json
    dd = Path.home() / 'xs-campaigns/2026-11-15-targets/P7/runs/s1'
    json.dump({'circuit': sys.argv[1], 'fs': [hex(f) for f in fs], 'decs': alldec},
              open(dd / ('alldec-%s.json' % Path(sys.argv[1]).name.split('.')[0]), 'w'))

    def opcost(prods):
        g = set()
        for (l, a, m, b, g1) in prods:
            for (x, p) in ((l, a), (m, b)):
                if bin(x).count('1') > 1 or p: g.add((x, p))
        return g

    # exhaustive over the product of choices (small) or greedy
    sizes = [len(d) for d in alldec]
    print('choices', sizes)
    best = None
    tot = 1
    for s in sizes: tot *= max(1, s)
    print('combinations', tot)
    if tot > 3_000_000:
        print('too many; skipping'); return
    for ch in itertools.product(*alldec):
        prods = set();
        for d in ch: prods.update(d)
        gates = opcost(prods) | bottom
        nsum = sum(len(d) - 1 for d in ch)
        cost = len(prods) + len(gates) + nsum
        if best is None or cost < best[0]:
            best = (cost, len(prods), len(gates), nsum, ch)
    cost, np_, ng, nsum, ch = best
    print('BEST: ANDs %d, top-layer gates %d (incl. %d bottom forms), N-sum XORs %d, total %d' % (np_, ng, len(bottom), nsum, cost))
    for k, d in enumerate(ch):
        print(' f%d:' % k, ' '.join('(%s%02x)(%s%02x)%s' % ('~' if a else '', l, '~' if b else '', m, '*' if g else '') for l, a, m, b, g in d))
    # the circuit's own
    own = set()
    for j, (op, a, b) in enumerate(c.gates):
        if op in L.core.NONLINEAR_OPS and la[c.n + j] == 1:
            pass
    print('reference: 59@10 has 17 AND-1 gates, 51 top-layer gates, 13 group-sum XORs')


if __name__ == '__main__':
    main()
