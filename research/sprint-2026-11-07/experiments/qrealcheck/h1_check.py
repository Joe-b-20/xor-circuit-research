#!/usr/bin/env python3
"""qrealcheck: independent recomputation of finite fact H1 (hub capacity) from the matrix file.

Written from PROOF.md (F2-F4, Lemma 4.4) and qreal/REPORT.md 1.1 only; nothing imported from qreal or the package.

Definitions used:
  B            = the 64 boundary masks: 32 unit vectors + the 32 rows of M (orientation M) or columns of M (M^T)
  pair value   = XOR of two distinct boundary masks (F2: 2,016 distinct values)
  triple value = XOR of three distinct boundary masks; full value = a value with exactly three such triples (F3/F4)
  N(h)         = { f full : h ^ f is a pair value }, for odd h not in B
  cap(h)       = largest |S|, S subset of N(h), such that the 3|S| formal vectors H_f + T (T over the three triples
                 of f, H_f a coordinate private to f) are linearly independent over GF(2)  (Lemma 4.4's notion)
Method: for every h, an exhaustive branch-and-bound DFS over N(h) with an incremental GF(2) basis over the 3|S|
vectors WITH explicit helper coordinates (bit 64 + position), not the two-line shortcut of hub.py.
Checks: histograms of |N(h)| and cap(h), kappa_0 (all h) and kappa_1 (triple values), cap by representation count,
the extremal sets, the pairwise-non-adjacency of every witness (F4), equivalence of the two independence notions on
random subsets, and the cross-check against qreal/hub_cap_{M,Mt}.json.
Output: qrealcheck/h1_cap_{M,Mt}.json  (cap(h) for every h with cap >= 1) and h1_check.log (stdout).
"""
import itertools, json, random, sys, time
from collections import Counter, defaultdict
from pathlib import Path
T0 = time.time()
def log(*a): print(f'[{time.time()-T0:6.1f}s]', *a, flush=True)

MAT = Path.home()/'xor-circuit-research/circuits/aes-mixcolumns/aes-mixcolumns.mat.txt'
OUT = Path.home()/'xs-campaigns/2026-11-07-sprint/qrealcheck'
QREAL = Path.home()/'xs-campaigns/2026-11-07-sprint/qreal'
lines = [l.split() for l in open(MAT).read().strip().split('\n') if l.strip()]
lines = lines[lines.index(['32', '32']):]
ROWS = [sum(int(b) << c for c, b in enumerate(l)) for l in lines[1:33]]
COLS = [sum(((ROWS[r] >> c) & 1) << r for r in range(32)) for c in range(32)]
assert len(ROWS) == 32 and all(bin(r).count('1') in (5, 7) for r in ROWS) and all(bin(c).count('1') in (5, 11) for c in COLS)
UNITS = [1 << i for i in range(32)]
BND = {'M': UNITS + ROWS, 'Mt': UNITS + COLS}

class Basis:
    __slots__ = ('piv',)
    def __init__(self, piv=None): self.piv = dict(piv) if piv else {}
    def reduce(self, v):
        piv = self.piv
        while v:
            hb = v.bit_length() - 1
            if hb in piv: v ^= piv[hb]
            else: return v
        return 0
    def add(self, v):
        v = self.reduce(v)
        if v: self.piv[v.bit_length() - 1] = v; return True
        return False
def rank(vs):
    b = Basis()
    for v in vs: b.add(v)
    return len(b.piv)

RESULT = {}
for ori in ('M', 'Mt'):
    B = BND[ori]; Bset = set(B)
    assert len(Bset) == 64 and all(bin(b).count('1') & 1 for b in B)
    pairs = {}
    for i, j in itertools.combinations(range(64), 2):
        v = B[i] ^ B[j]; assert v not in pairs, 'F2 fails'; pairs[v] = (i, j)
    assert len(pairs) == 2016
    trip = defaultdict(list)
    for i, j, k in itertools.combinations(range(64), 3):
        trip[B[i] ^ B[j] ^ B[k]].append((1 << i) | (1 << j) | (1 << k))
    mult = Counter(len(t) for t in trip.values())
    log(ori, 'F3 triple multiplicities', dict(sorted(mult.items())))
    assert max(mult) == 3
    full = {v: ts for v, ts in trip.items() if len(ts) == 3}
    nfull = len(full); assert nfull == (80 if ori == 'M' else 112)
    fulls = sorted(full)
    # N(h): h = f ^ p over full f and pair values p; keep odd h outside B (all f ^ p are odd: odd + even)
    N = defaultdict(set)
    for f in fulls:
        for p in pairs:
            hh = f ^ p
            if hh not in Bset: N[hh].add(f)
    assert all(bin(hh).count('1') & 1 for hh in N)
    hist_N = Counter(len(s) for s in N.values())
    log(ori, 'candidate h:', len(N), '|N(h)| histogram', dict(sorted(hist_N.items())))

    # relation vectors of f with helper coordinate slot k: three vectors T | 1 << (64 + k)
    def relvecs(f, k): return [t | (1 << (64 + k)) for t in full[f]]

    def cap_dfs(fs):
        """exhaustive: maximum independent subset of fs (3|S| relation vectors with private helper coordinates)."""
        fs = sorted(fs); n = len(fs); best = [0, ()]
        def rec(idx, basis, chosen):
            if len(chosen) > best[0]: best[0] = len(chosen); best[1] = tuple(chosen)
            if len(chosen) + (n - idx) <= best[0]: return
            for t in range(idx, n):
                if len(chosen) + (n - t) <= best[0]: return
                f = fs[t]; nb = Basis(basis.piv); ok = True
                for v in relvecs(f, len(chosen)):
                    if not nb.add(v): ok = False; break
                if ok:
                    chosen.append(f); rec(t + 1, nb, chosen); chosen.pop()
        rec(0, Basis(), [])
        return best[0], best[1]

    cap = {}; wit = {}
    for hh, fs in N.items():
        c, S = cap_dfs(fs); cap[hh] = c; wit[hh] = S
    hist_cap = Counter(cap.values())
    tripvals = set(trip)
    cap_trip = {hh: c for hh, c in cap.items() if hh in tripvals}
    hist_cap_trip = Counter(cap_trip.values())
    kappa0 = max(cap.values()); kappa1 = max(cap_trip.values())
    log(ori, 'cap histogram (all odd non-boundary h with N(h) nonempty):', dict(sorted(hist_cap.items())))
    log(ori, 'cap histogram (triple values):', dict(sorted(hist_cap_trip.items())))
    log(ori, 'kappa_0 =', kappa0, ' kappa_1 =', kappa1)
    by_rep = {}
    for m in (0, 1, 2, 3):
        hs = {hh: c for hh, c in cap.items() if len(trip.get(hh, [])) == m}
        by_rep[m] = (len(hs), dict(sorted(Counter(hs.values()).items())), max(hs.values()) if hs else 0)
        log(ori, f'  h with {m} triple representation(s): {len(hs)} values, cap histogram {by_rep[m][1]}, max {by_rep[m][2]}')
    # the claim: cap <= 2 unless h is a repeated value with exactly two representations
    viol = [hh for hh, c in cap.items() if c > 2 and len(trip.get(hh, [])) != 2]
    log(ori, 'values with cap > 2 that are not 2-representation values:', len(viol))
    cap4 = sorted(hh for hh, c in cap.items() if c == 4)
    log(ori, 'values with cap 4:', len(cap4), [hex(v) for v in cap4])
    # every witness: pairwise non-adjacent (F4) and the 3|S| vectors independent (re-verified with a fresh rank call)
    bad = 0
    for hh, S in wit.items():
        if len(S) < 2: continue
        vecs = [v for k, f in enumerate(S) for v in relvecs(f, k)]
        if rank(vecs) != 3 * len(S): bad += 1
        for a, b in itertools.combinations(S, 2):
            if (a ^ b) in pairs: bad += 1
        # the pairs h ^ f are pairwise distinct boundary pairs
        if len({hh ^ f for f in S}) != len(S): bad += 1
    log(ori, 'witness re-verification failures (rank, adjacency, distinct pairs):', bad)
    # maximality cross-check by a second method: for the h with |N(h)| >= 4, brute force over all subsets of size cap+1
    bad2 = 0; tested = 0
    for hh, fs in N.items():
        if len(fs) <= cap[hh]: continue
        tested += 1
        for S in itertools.combinations(sorted(fs), cap[hh] + 1):
            vecs = [v for k, f in enumerate(S) for v in relvecs(f, k)]
            if rank(vecs) == 3 * len(S): bad2 += 1; break
    log(ori, 'second method (all subsets of size cap+1 dependent):', tested, 'values tested,', bad2, 'failures')
    # equivalence of the two independence notions on random subsets of N(h) (3|S| relation vectors vs 2|S| line vectors)
    rng = random.Random(5); mism = 0
    big = [hh for hh, fs in N.items() if len(fs) >= 3]
    for _ in range(3000):
        hh = rng.choice(big); fs = sorted(N[hh]); S = rng.sample(fs, rng.randint(2, min(5, len(fs))))
        r1 = rank([v for k, f in enumerate(S) for v in relvecs(f, k)]) == 3 * len(S)
        r2 = rank([full[f][0] ^ full[f][1] for f in S] + [full[f][0] ^ full[f][2] for f in S]) == 2 * len(S)
        if r1 != r2: mism += 1
    log(ori, 'independence-notion equivalence mismatches on 3000 random subsets:', mism)
    # cross-check with qreal
    ref = json.load(open(QREAL/f'hub_cap_{ori}.json'))
    refcap = {int(k): v for k, v in ref['cap'].items()}
    mine = {hh: c for hh, c in cap.items() if c >= 1}
    diff = {hh for hh in set(mine) | set(refcap) if mine.get(hh, 0) != refcap.get(hh, 0)}
    log(ori, f'cross-check with qreal hub_cap: kappa0 {ref["kappa0"]} kappa1 {ref["kappa1"]}; values with cap>=1: mine {len(mine)} ref {len(refcap)}; differing {len(diff)}')
    assert kappa0 == 4 and kappa1 == 4 and not diff and bad == 0 and bad2 == 0 and mism == 0 and not viol
    json.dump({'kappa0': kappa0, 'kappa1': kappa1, 'hist_N': dict(hist_N), 'hist_cap': dict(hist_cap), 'hist_cap_trip': dict(hist_cap_trip),
               'by_rep': {str(m): v for m, v in by_rep.items()}, 'cap4': [hex(v) for v in cap4],
               'cap': {str(hh): c for hh, c in mine.items()}}, open(OUT/f'h1_cap_{ori}.json', 'w'))
    RESULT[ori] = (kappa0, kappa1, dict(hist_cap), dict(hist_cap_trip))
log('H1 CHECK PASSED', RESULT)
