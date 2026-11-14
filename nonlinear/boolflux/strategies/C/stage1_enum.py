"""Exhaustive stage-1 bound via the cover lemma (NOTES.md section 7) and the orbit reduction.

k = 7: fix P1 to each of the 8 orbit representatives; U = V_N + P1 (d = 5); the other 6 products
have images in Lambda^2/U spanning <= 2 dims -> cover_enum (exact).
k = 8: P1 representative, P2 any rank-2 form not in V_N + P1; U = V_N + P1 + P2 (d = 6), the other
6 products have images spanning <= 2 dims -> cover_enum (exact). (Slow; --p2-limit for tests.)

usage: python3 stage1_enum.py 7 | 8 [--rep i] [--p2-start s --p2-end e]
"""
from __future__ import annotations

import argparse
import itertools
import json
import time

import gf
import cover_enum
import stage1
import wsat

PAIRS = list(itertools.combinations(range(8), 2))


def wedge(l, m):
    w = 0
    for k, (i, j) in enumerate(PAIRS):
        if (l[i] & m[j]) ^ (l[j] & m[i]): w |= 1 << k
    return w


def orbit_labels(R, reps):
    """orbit index (0..7, same order as stage1.orbit_reps) of every rank-2 form, by BFS under
    the generators x -> 3x and x -> x^2 acting on linear forms."""
    def lin_map(g):
        # coefficient vector (8 bits, U0 = msb) of x -> l_c(g(x)) for each c
        out = {}
        for c in range(1, 256):
            cv = [(c >> (7 - i)) & 1 for i in range(8)]
            def l(x): return sum(cv[i] & ((x >> (7 - i)) & 1) for i in range(8)) & 1
            v = 0
            for i in range(8):
                if l(g(1 << (7 - i))): v |= 1 << (7 - i)
            out[c] = v
        return out
    gens = [lin_map(lambda x: gf.mul(3, x)), lin_map(lambda x: gf.mul(x, x))]
    # wedge from pair of coefficient ints
    def wd(a, b):
        return wedge([(a >> (7 - i)) & 1 for i in range(8)], [(b >> (7 - i)) & 1 for i in range(8)])
    pair_of = {}
    for a in range(1, 256):
        for b in range(a + 1, 256):
            pair_of.setdefault(wd(a, b), (a, b))
    label = {}
    for idx, (la, lb, sz) in enumerate(reps):
        a = int(''.join(map(str, la)), 2); b = int(''.join(map(str, lb)), 2)
        start = wd(a, b)
        if start in label: continue
        stack = [start]; label[start] = idx
        while stack:
            w = stack.pop(); a, b = pair_of[w]
            for gm in gens:
                w2 = wd(gm[a], gm[b])
                if w2 not in label:
                    label[w2] = idx; stack.append(w2)
    return label


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('k', type=int)
    ap.add_argument('--rep', type=int, default=None)
    ap.add_argument('--p2-start', type=int, default=0)
    ap.add_argument('--p2-end', type=int, default=10795)
    a = ap.parse_args()
    Nf = wsat.n_forms()
    reps = stage1.orbit_reps()
    R = cover_enum.rank2_forms()
    t0 = time.time()
    for i, (la, lb, sz) in enumerate(reps):
        if a.rep is not None and i != a.rep: continue
        P1 = wedge(la, lb)
        if a.k == 7:
            info, found = cover_enum.run(Nf + [P1], 7)
            print(json.dumps({'k': 7, 'rep': i, 'found': info['found'], 'info': info,
                              'secs': round(time.time() - t0, 1)}), flush=True)
            if found: return
        else:
            hits = 0
            lab = orbit_labels(R, reps)
            sizes = {}
            for v in lab.values(): sizes[v] = sizes.get(v, 0) + 1
            print(json.dumps({'labels': len(lab), 'orbit_sizes': sizes}), flush=True)
            for j in range(a.p2_start, min(a.p2_end, len(R))):
                P2 = R[j]
                if lab[P2] < i or P2 == P1: continue      # P1 = product of least orbit index
                if gf.Span(Nf + [P1]).contains(P2): continue
                info, found = cover_enum.run(Nf + [P1, P2], 8)
                if found:
                    hits += 1
                    print(json.dumps({'k': 8, 'rep': i, 'p2': j, 'FOUND': True, 'info': info}), flush=True)
                    return
                if j % 500 == 0:
                    print(json.dumps({'k': 8, 'rep': i, 'p2': j, 'secs': round(time.time() - t0, 1),
                                      'last': {kk: info.get(kk) for kk in ('in_U', 'y1_candidates', 'plane_tests')}}),
                          flush=True)
            print(json.dumps({'k': 8, 'rep': i, 'done': True, 'range': [a.p2_start, a.p2_end],
                              'secs': round(time.time() - t0, 1)}), flush=True)


if __name__ == '__main__':
    main()
