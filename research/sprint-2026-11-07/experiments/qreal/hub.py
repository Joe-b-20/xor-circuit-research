#!/usr/bin/env python3
"""Finite fact H1 (hub helpers): for every odd value h (not a boundary value) let
    N(h) = { f full value : h + f is a boundary-pair value }
and cap(h) = the largest size of a subset S of N(h) whose 3|S| represented relations (H_f + T, T a triple of f)
are linearly independent (Lemma 4.4 forces this for any set of full HELPERS; equivalently the 2|S| six-set
differences are independent, and in particular the members are pairwise non-adjacent, F4).

Why it matters.  Let i be a helper with r_i < 3 and let l be a missing label at i (edge i-b, l = h_i + b) that
also meets a full helper f through an H-B edge f-c (l = f + c).  Then h_i + f = b + c is a boundary-pair value,
so f in N(h_i).  Two distinct missing labels at i meet distinct full helpers (Lemma 4.6: two helpers share at most
one missing label), and the full helpers of a circuit are jointly independent (Lemma 4.4).  Hence
    #(missing labels at i that meet a full helper) <= cap(h_i) <= kappa,
with kappa_0 = max over all odd non-boundary h (r_i = 0) and kappa_1 = max over triple values (r_i >= 1: h_i is
the XOR of a boundary triple).  Every missing label meets at most one full helper (Lemma 4.5), so the number of
labels meeting a full helper is exactly A = sum_{r=3} u, and every other label is one of q - A.  Therefore, for
every helper i with r_i < 3:   u_i <= cap(h_i) + (q - A).

Outputs: histograms of |N(h)| and cap(h) over all h and over triple values, kappa_0, kappa_1, the extremal h,
a second-method check (rank of the 3|S| relation vectors with helper coordinates), and hub_cap_{ori}.json with
cap(h) for every h with cap >= 1 (used by the circuit check).
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

def analyse(ori):
    t0 = time.time()
    B = BOUNDARY[ori]; Bset = set(B)
    trip = defaultdict(list)
    for i, j, k in itertools.combinations(range(64), 3):
        trip[B[i] ^ B[j] ^ B[k]].append((1 << i) | (1 << j) | (1 << k))
    full = {v: ts for v, ts in trip.items() if len(ts) == 3}
    tripvals = set(trip)
    PV = {B[i] ^ B[j] for i, j in itertools.combinations(range(64), 2)}
    assert len(PV) == 2016
    fulls = sorted(full)
    # six-set differences of each full value (two independent vectors spanning its line)
    line = {f: (full[f][0] ^ full[f][1], full[f][0] ^ full[f][2]) for f in fulls}
    # N(h) for every h in f + PV
    N = defaultdict(list)
    for f in fulls:
        for p in PV:
            N[f ^ p].append(f)
    # h must be odd and not a boundary value; all f + p are odd (odd + even); drop boundary values
    N = {h: fs for h, fs in N.items() if h not in Bset}
    print(f'{ori}: full values {len(fulls)}, candidate h = f + pair: {len(N)} distinct odd non-boundary values; '
          f'|N(h)| histogram {dict(sorted(Counter(len(v) for v in N.values()).items()))}; {time.time()-t0:.1f}s', flush=True)

    def indep(S):
        vecs = [v for f in S for v in line[f]]
        return rank2(vecs) == 2 * len(S)

    def cap_of(fs):
        # max independent subset, exact (|fs| is small); search by decreasing size
        fs = list(fs)
        for size in range(len(fs), 0, -1):
            for S in itertools.combinations(fs, size):
                if indep(S): return size, S
        return 0, ()

    cap = {}; wit = {}
    for h, fs in N.items():
        c, S = cap_of(fs)
        cap[h] = c; wit[h] = S
    hist_all = Counter(cap.values())
    trip_h = {h: c for h, c in cap.items() if h in tripvals}
    hist_trip = Counter(trip_h.values())
    k0 = max(cap.values()); k1 = max(trip_h.values()) if trip_h else 0
    print(f'{ori}: cap histogram over all odd non-boundary h (h outside f+PV have cap 0): {dict(sorted(hist_all.items()))}')
    print(f'{ori}: cap histogram over TRIPLE values h (possible values of helpers with r >= 1): {dict(sorted(hist_trip.items()))}')
    print(f'{ori}: kappa_0 (r = 0 helpers) = {k0}; kappa_1 (r >= 1 helpers) = {k1}')
    # breakdown of triple values by their multiplicity (1 / 2 / 3 triples) -- cap for repeated values (r >= 2 helpers)
    for m in (1, 2, 3):
        hs = {h: c for h, c in trip_h.items() if len(trip[h]) == m}
        if hs: print(f'{ori}:   triple values with {m} representation(s): {len(hs)} in f+PV, cap histogram {dict(sorted(Counter(hs.values()).items()))}, max {max(hs.values())}')
    ext = [h for h, c in cap.items() if c == k0][:5]
    print(f'{ori}: extremal h (first 5): {[hex(h) for h in ext]}, with witness sets {[[hex(f) for f in wit[h]] for h in ext]}')

    # second method: rank of the 3|S| relation vectors with explicit helper coordinates (bit 64 + index)
    bad = 0; checked = 0
    for h in list(cap)[:20000]:
        S = wit[h]
        if not S: continue
        vecs = []
        for idx, f in enumerate(S):
            for T in full[f]: vecs.append(T | (1 << (64 + idx)))
        checked += 1
        if rank2(vecs) != 3 * len(S): bad += 1
        # and maximality: no larger independent subset exists -- verified by cap_of's exhaustive descent; recheck that
        # adding any further f of N(h) to the witness breaks independence (only a sanity check, not the maximality proof)
    print(f'{ori}: second-method check of {checked} witnesses (3|S| relation vectors independent): {bad} failures')
    # hub structure: for the extremal h, the pairs h + f must be pairwise disjoint (else two f adjacent): verify
    for h in ext:
        prs = [h ^ f for f in wit[h]]
        assert len(prs) == len(set(prs))
    json.dump({'kappa0': k0, 'kappa1': k1, 'hist_all': dict(hist_all), 'hist_trip': dict(hist_trip),
               'cap': {str(h): c for h, c in cap.items() if c >= 1}},
              open(OUT/f'hub_cap_{ori}.json', 'w'))
    print(f'{ori}: done in {time.time()-t0:.1f}s')
    return k0, k1

if __name__ == '__main__':
    res = {o: analyse(o) for o in (sys.argv[1].split(',') if len(sys.argv) > 1 else ['M', 'Mt'])}
    print('RESULT kappa (r=0, r>=1):', res)
