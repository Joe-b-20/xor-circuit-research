#!/usr/bin/env python3
"""Finite fact FM (full-met labels): for every full value f and boundary element c (c not in the triples of f, else
f + c is a boundary pair and not a missing label... it may still be: a pair value without its gate), the label
l = f + c has rank(C_l) (F6: span of E_l + sum_D B_b over 2/4-subsets D with XOR l).  The three forms E_l + T + B_c
(T a triple of f) lie in C_l, so rank(C_l) >= 3 (if c is outside the triples).  At a missing label l met by a full
helper f through f-c, PROOF's (L7) argument gives  W_l + Y_l <= rank(C_l), and (L15)'s  Z_l <= rank(C_l) - 1 - k_l.
Hence, with A = sum_{r=3} u (full-met labels, one full helper each) and top_full(A) = sum of the A largest ranks
over all labels f + c:
    (FM7)  W + y_1 <= 7 (q - A) + top_full(A)        (replaces L7*)
    (FM9)  Z <= 3 (q - A) + sum_{full-met} min(3, rank - 1) <= 3 (q - A) + top3_full(A)  (replaces L9)
where top3_full(A) = sum of the A largest values of min(3, rank(C_l) - 1) over labels f + c.
This script prints the rank histogram over the pairs (f, c), over distinct labels, and the top tables.
"""
import sys, json, itertools, time
from collections import Counter, defaultdict
from pathlib import Path
sys.path.insert(0, str(Path.home()/'xs-campaigns/2026-11-07-sprint/lb76/pkg_copy/source/lower_bounds/checks'))
from stress import BOUNDARY  # noqa: E402
OUT = Path.home()/'xs-campaigns/2026-11-07-sprint/qreal'

def rank2(vectors):
    piv = {}
    for v in vectors:
        while v:
            hb = v.bit_length() - 1
            if hb in piv: v ^= piv[hb]
            else: piv[hb] = v; break
    return len(piv)

def main(ori):
    t0 = time.time()
    B = BOUNDARY[ori]
    trip = defaultdict(list)
    for i, j, k in itertools.combinations(range(64), 3):
        trip[B[i] ^ B[j] ^ B[k]].append((1 << i) | (1 << j) | (1 << k))
    fulls = sorted(v for v, ts in trip.items() if len(ts) == 3)
    forms = defaultdict(list)
    for i, j in itertools.combinations(range(64), 2): forms[B[i] ^ B[j]].append((1 << i) | (1 << j))
    for S in itertools.combinations(range(64), 4):
        v = 0; m = 0
        for i in S: v ^= B[i]; m |= 1 << i
        forms[v].append(m)
    print(f'{ori}: forms built, {time.time()-t0:.0f}s', flush=True)
    def rankC(l):
        fs = forms.get(l, [])
        # rank of E_l + D over D: = 1 + rank of differences (if any form exists)
        if not fs: return 0
        return 1 + rank2([fs[0] ^ f for f in fs[1:]])
    labels = {}
    pairs_hist = Counter(); in_trip = 0
    for f in fulls:
        supp = trip[f][0] | trip[f][1] | trip[f][2]
        for ci, c in enumerate(B):
            l = f ^ c
            if l not in labels: labels[l] = rankC(l)
            if (supp >> ci) & 1: in_trip += 1
            pairs_hist[(labels[l], bool((supp >> ci) & 1))] += 1
    ranks = sorted(labels.values(), reverse=True)
    hist = Counter(labels.values())
    print(f'{ori}: {len(labels)} distinct labels f + c (f full, c in B); rank(C_l) histogram: {dict(sorted(hist.items()))}; '
          f'(pairs (f,c) with c inside a triple of f: {in_trip}; their (rank, inside) histogram: {dict(sorted(pairs_hist.items()))})', flush=True)
    # which labels can be MISSING labels met by a full helper?  l = f + c: if c is in a triple T of f then l = T \ {c}
    # is a boundary-pair value; it can be a missing label only if its pair gate is absent.  Keep all.
    top = [sum(ranks[:a]) for a in range(0, 15)]
    r3 = sorted((min(3, r - 1) for r in labels.values()), reverse=True)
    top3 = [sum(r3[:a]) for a in range(0, 15)]
    print(f'{ori}: top_full(A) = {top}')
    print(f'{ori}: top3_full(A) = {top3}')
    # per full value: the max rank over its 64 labels, and how many of its labels have rank >= 4
    per_f = Counter(max(labels[f ^ c] for c in B) for f in fulls)
    ge4 = Counter(sum(1 for c in B if labels[f ^ c] >= 4) for f in fulls)
    print(f'{ori}: per full value: max rank over its labels histogram {dict(sorted(per_f.items()))}; number of labels with rank >= 4 histogram {dict(sorted(ge4.items()))}')
    json.dump(dict(ori=ori, hist=dict(hist), top=top, top3=top3), open(OUT/f'fullmet_{ori}.json', 'w'))
    print(f'{ori}: done {time.time()-t0:.0f}s')

if __name__ == '__main__':
    for o in (sys.argv[1].split(',') if len(sys.argv) > 1 else ['M', 'Mt']): main(o)
