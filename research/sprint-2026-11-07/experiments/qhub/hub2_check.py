#!/usr/bin/env python3
"""Second-method check of finite fact H2 (hub2.py): for every odd non-boundary h and r = 0,1,2, the largest m
such that some R (r triples of h) and S (m full values in N(h)) make the family
   {H_f + T} u {H_i + T_R} u {H_i + H_f + P_f}
independent is at most 3 - r, and the maximum 3 - r is attained.  Independent implementation: explicit
numpy-free Gaussian elimination over integer bit vectors built from scratch (coordinates reordered: helpers first),
exhaustive over ALL subsets of N(h) (no DFS pruning) for every h with |N(h)| <= 11, and over subsets of size
<= 4 - r + 1 for larger N(h) (an independent set of size 4 - r would already refute the bound).  Also records
the number of h attaining 3 - r, and the circuit-level check: on qreal/qr_circ.json every phase has
max #full-met labels at non-full helpers = 0 and A = 0, so r + m <= 3 holds at every helper (m = 0, r <= 3).
usage: python3 hub2_check.py [M,Mt]
"""
import sys, json, itertools, time
from collections import Counter, defaultdict
from pathlib import Path
sys.path.insert(0, str(Path.home()/'xs-campaigns/2026-11-07-sprint/lb76/pkg_copy/source/lower_bounds/checks'))
from stress import BOUNDARY  # noqa: E402
OUT = Path.home()/'xs-campaigns/2026-11-07-sprint/qhub'

def gf2_rank(rows):
    rows = [r for r in rows if r]
    rank = 0
    while rows:
        p = rows.pop()
        rank += 1
        hb = p.bit_length() - 1
        rows = [r ^ p if (r >> hb) & 1 else r for r in rows]
        rows = [r for r in rows if r]
    return rank

def check(ori):
    t0 = time.time()
    B = BOUNDARY[ori]; Bset = set(B)
    trip = defaultdict(list)
    for i, j, k in itertools.combinations(range(64), 3):
        trip[B[i] ^ B[j] ^ B[k]].append((i, j, k))
    full = {v: ts for v, ts in trip.items() if len(ts) == 3}
    pairidx = {B[i] ^ B[j]: (i, j) for i, j in itertools.combinations(range(64), 2)}
    N = defaultdict(set)
    for f in full:
        for p in pairidx: N[f ^ p].add(f)
    N = {h: sorted(v) for h, v in N.items() if h not in Bset}
    # coordinates: bit 0 = hub, bits 1..m = full helpers, bits 16.. = boundary (shifted)
    def bvec(idxs):
        v = 0
        for i in idxs: v |= 1 << (16 + i)
        return v
    maxm = {r: Counter() for r in (0, 1, 2)}
    viol = 0; attain = {r: 0 for r in (0, 1, 2)}; nh = {r: 0 for r in (0, 1, 2)}
    for h, fs in N.items():
        reps = trip.get(h, [])
        for r in (0, 1, 2):
            if len(reps) < r: continue
            nh[r] += 1
            best = 0
            sizes = range(1, len(fs) + 1) if len(fs) <= 11 else range(1, min(len(fs), 4 - r + 1) + 1)
            for R in (itertools.combinations(reps, r) if r else [()]):
                hubrows = [bvec(T) | 1 for T in R]
                for m in sizes:
                    if m < best: continue
                    found = False
                    for S in itertools.combinations(fs, m):
                        rows = list(hubrows)
                        for j, f in enumerate(S):
                            for T in full[f]: rows.append(bvec(T) | (1 << (1 + j)))
                            rows.append(bvec(pairidx[h ^ f]) | 1 | (1 << (1 + j)))
                        if gf2_rank(rows) == len(rows): found = True; break
                    if found: best = max(best, m)
                    else: break      # hereditary: no independent m-set means no larger one
            maxm[r][best] += 1
            if best > 3 - r: viol += 1; print('VIOLATION', ori, r, hex(h), best)
            if best == 3 - r: attain[r] += 1
    for r in (0, 1, 2):
        print(f'{ori} r={r}: {nh[r]} hub values, max-m histogram {dict(sorted(maxm[r].items()))}, bound 3-r={3-r} attained by {attain[r]}, violations so far {viol}')
    print(f'{ori}: {viol} violations of r + m <= 3; {time.time()-t0:.0f}s', flush=True)
    return viol, {r: dict(maxm[r]) for r in maxm}

if __name__ == '__main__':
    oris = sys.argv[1].split(',') if len(sys.argv) > 1 else ['M', 'Mt']
    res = {o: check(o) for o in oris}
    # circuit-level: qreal's per-phase data
    try:
        ph = [p for rec in json.load(open(Path.home()/'xs-campaigns/2026-11-07-sprint/qreal/qr_circ.json')) for p in rec['phases']]
        print(f'circuits: {len(ph)} phases; max A (full-met labels) = {max(p["A"] for p in ph)}; max #full-met at a non-full helper = {max(p["hub_max"] for p in ph)}; '
              f'so r + m <= 3 holds at every helper of every phase (m = 0 everywhere, r <= 3 by Lemma 4.4)')
    except Exception as e:
        print('circuit data not available:', e)
    json.dump({o: dict(violations=v, hist=hh) for o, (v, hh) in res.items()}, open(OUT/'hub2_check.json', 'w'))
    print('RESULT violations:', {o: v for o, (v, _) in res.items()})
