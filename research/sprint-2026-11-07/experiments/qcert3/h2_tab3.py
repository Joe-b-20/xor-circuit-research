#!/usr/bin/env python3
"""qcert3/h2_tab3.py -- recomputation of finite fact H2 (PROOF_ADDENDUM_3.md C.2), standard library only, own code.

From the definitions: boundary B parsed from the repository's aes-mixcolumns.mat.txt (fm_tab3.read_boundary); pair
values with their unique pair (F2); the 3-subsets of B by XOR, full values = exactly three (F3); N(h) = {f full : h + f a
pair value} for odd h not in B; for r in {0, 1, 2}, every r-subset R of the triples of h and every S subset of N(h):
  F(h, R, S) = {H_f + T : f in S, T triple of f} u {H_i + T : T in R} u {H_i + H_f + P_f : f in S},
cap_r(h) = the largest |S| with F(h, R, S) independent for some R.  Enumeration: depth-first extension of S in
increasing order of N(h) (independence is hereditary in S), the rank recomputed at every node by a fresh fully reduced
GF(2) elimination (fm_tab3.Reduced): no incremental basis, no undo, no pruning by size.  Coordinates: boundary index
i -> bit i, hub -> bit 64, full helper j (position in S) -> bit 65 + j.
Also: H1 (the 3|S| vectors H_f + T alone) for the same h, and a per-value comparison with qhub's hub2_{ori}.json.
usage: nice -n 8 python3 h2_tab3.py [M,Mt]       (writes h2_tab3.json)
"""
import sys, json, itertools, time
from collections import Counter, defaultdict
from pathlib import Path
SPRINT = Path.home() / 'xs-campaigns/2026-11-07-sprint'
HERE = SPRINT / 'qcert3'
sys.path.insert(0, str(HERE))
from fm_tab3 import read_boundary, Reduced   # noqa: E402  (own code of this directory)
HUB = 1 << 64
def FC(j): return 1 << (65 + j)
EXPECTED = {'M': {0: {1: 126412, 2: 1648, 3: 8}, 1: {0: 11392, 1: 1124, 2: 64}, 2: {0: 428, 1: 12}},
            'Mt': {0: {1: 174320, 2: 3072, 3: 20}, 1: {0: 15216, 1: 1804, 2: 120}, 2: {0: 592, 1: 24}}}   # qhub hub2.log / qhubcheck h2_check.log
EXPECTED_H1 = {'M': {1: 125128, 2: 2840, 3: 92, 4: 8}, 'Mt': {1: 172060, 2: 5156, 3: 176, 4: 20}}


def independent(vectors):
    R = Reduced()
    return all(R.add(v) for v in vectors)


def cap_r(h, R, N, full, pairmask, mixed=True):
    """largest |S| (S subset of N, index-increasing DFS) with F(h, R, S) independent; also the number of maximal S."""
    hubrows = [t | HUB for t in R]
    best = [0, 0]
    def fam(S):
        rows = list(hubrows)
        for j, f in enumerate(S):
            rows += [t | FC(j) for t in full[f]]
            if mixed: rows.append(pairmask[h ^ f] | HUB | FC(j))
        return rows
    def rec(start, S):
        if len(S) > best[0]: best[0] = len(S); best[1] = 0
        if len(S) == best[0]: best[1] += 1
        for k in range(start, len(N)):
            S2 = S + [N[k]]
            if independent(fam(S2)): rec(k + 1, S2)
    rec(0, [])
    return best[0], best[1]


def main(ori):
    t0 = time.time()
    B = read_boundary(ori); Bset = set(B)
    pairmask = {}
    for i, j in itertools.combinations(range(64), 2):
        v = B[i] ^ B[j]; assert v not in pairmask; pairmask[v] = (1 << i) | (1 << j)
    trip = defaultdict(list)
    for i, j, k in itertools.combinations(range(64), 3): trip[B[i] ^ B[j] ^ B[k]].append((1 << i) | (1 << j) | (1 << k))
    full = {v: ts for v, ts in trip.items() if len(ts) == 3}
    N = defaultdict(list)
    for f in sorted(full):
        for p in pairmask:
            h = f ^ p
            if h not in Bset: N[h].append(f)
    print(f'{ori}: {len(full)} full values, {len(N)} odd non-boundary h with N(h) nonempty, |N(h)| histogram {dict(sorted(Counter(len(v) for v in N.values()).items()))}; {time.time()-t0:.0f}s', flush=True)
    res = {}; caps = {}
    for r in (0, 1, 2):
        hist = Counter(); att = 0; viol = []; nconf = 0
        for h, fs in N.items():
            reps = trip.get(h, [])
            if len(reps) < r: continue
            best = 0
            for Rr in (itertools.combinations(reps, r) if r else [()]):
                if r and not independent([t | HUB for t in Rr]): continue
                c, nmax = cap_r(h, Rr, fs, full, pairmask)
                if c > best: best = c
            hist[best] += 1; caps[(r, h)] = best
            if best == 3 - r: att += 1
            if best > 3 - r: viol.append(hex(h))
        print(f'{ori} r={r}: {sum(hist.values())} hub values; cap_r histogram {dict(sorted(hist.items()))}; attaining 3-r: {att}; violations of cap_r <= 3-r: {len(viol)} {viol[:3]}; '
              f'equals the qhub / qhubcheck histogram: {dict(hist) == EXPECTED[ori][r]}; {time.time()-t0:.0f}s', flush=True)
        assert not viol and dict(hist) == EXPECTED[ori][r], (ori, r, dict(hist))
        res[r] = dict(hist=dict(hist), attaining=att, violations=len(viol))
    # H1 cross-check: the 3|S| vectors alone
    h1 = Counter()
    for h, fs in N.items(): h1[cap_r(h, (), fs, full, pairmask, mixed=False)[0]] += 1
    print(f'{ori}: H1 (3|S| vectors only) histogram {dict(sorted(h1.items()))}; equals finite fact H1: {dict(h1) == EXPECTED_H1[ori]}; {time.time()-t0:.0f}s', flush=True)
    assert dict(h1) == EXPECTED_H1[ori]
    # per-value comparison with qhub's table (c1 = capacity under C1, max over R)
    tab = json.load(open(SPRINT / f'qhub/hub2_{ori}.json'))['cap']
    diff = 0; compared = 0
    for r in (0, 1, 2):
        t = {int(h): b['c1'] for h, b in tab[str(r)].items()}
        for (rr, h), c in caps.items():
            if rr != r: continue
            compared += 1
            if t.get(h, 0) != c: diff += 1
    print(f'{ori}: per-value comparison with qhub hub2_{ori}.json: {compared} (r, h) values compared, {diff} differ; {time.time()-t0:.0f}s', flush=True)
    assert diff == 0
    return dict(hub_values=len(N), per_r=res, h1_hist=dict(h1), compared_with_qhub=compared, differing=diff, seconds=time.time() - t0)


if __name__ == '__main__':
    oris = sys.argv[1].split(',') if len(sys.argv) > 1 else ['M', 'Mt']
    out = {o: main(o) for o in oris}
    json.dump(out, open(HERE / 'h2_tab3.json', 'w'), indent=1)
    print('H2 RECOMPUTED: histograms identical to qhub and qhubcheck, 0 violations, per-value capacities identical to the qhub table')
