#!/usr/bin/env python3
"""Finite fact (new): for a boundary pair P = {b, c} let sigma(P) = rank of the set of weight-6 zero-sum boundary
subsets containing P (equivalently rank(C_l) - 1 for the pair value l = b + c, since by F2 every 4-form of a
pair value is disjoint from its pair).  At a represented label l with B-B edge P, the helpers i meeting l
through an H-B edge contribute sum_i (r_i - 1)_+ independent six-sets containing P (differences of represented
relations, Lemma 4.4), so sum_{i meets l} (r_i - 1)_+ <= sigma(P_l).
Outputs: histogram of sigma over the 2016 pairs, the number of six-sets containing each pair, and the table
top(m) = sum of the m largest sigma values (m = 0..64), for M and Mt.
"""
import sys, json, itertools
from collections import Counter, defaultdict
from pathlib import Path
sys.path.insert(0, str(Path.home()/'xs-campaigns/2026-11-07-sprint/lb76/pkg_copy/source/lower_bounds/checks'))
from stress import BOUNDARY  # noqa: E402

def rank2(vectors):
    piv = {}
    for v in vectors:
        while v:
            h = v.bit_length() - 1
            if h in piv: v ^= piv[h]
            else: piv[h] = v; break
    return len(piv)

out = {}
for name in ('M', 'Mt'):
    B = BOUNDARY[name]
    trip = defaultdict(list)
    for i, j, k in itertools.combinations(range(64), 3):
        trip[B[i] ^ B[j] ^ B[k]].append((1 << i) | (1 << j) | (1 << k))
    six = set()
    for ts in trip.values():
        if len(ts) >= 2:
            for a, b in itertools.combinations(ts, 2): six.add(a | b)
    pairs = {}
    for i, j in itertools.combinations(range(64), 2):
        P = (1 << i) | (1 << j)
        S = [s for s in six if s & P == P]
        pairs[(i, j)] = (len(S), rank2(S))
    hist_m = Counter(v[0] for v in pairs.values()); hist_s = Counter(v[1] for v in pairs.values())
    sig = sorted((v[1] for v in pairs.values()), reverse=True)
    top = [sum(sig[:m]) for m in range(65)]
    # which pairs are rich: input-input, input-output, output-output
    kind = Counter()
    for (i, j), (m, s) in pairs.items():
        k = ('in' if i < 32 else 'out') + '-' + ('in' if j < 32 else 'out')
        kind[(k, s)] += 1
    print(f'{name}: six-sets {len(six)}; pairs by #six-sets containing them: {dict(sorted(hist_m.items()))}')
    print(f'{name}: pairs by sigma (rank): {dict(sorted(hist_s.items()))}; pairs with sigma>=1: {sum(v for k, v in hist_s.items() if k >= 1)}, sigma>=2: {sum(v for k, v in hist_s.items() if k >= 2)}')
    print(f'{name}: pairs by (kind, sigma): {dict(sorted(kind.items()))}')
    print(f'{name}: top(m) = sum of m largest sigma: ' + ' '.join(f'{m}:{top[m]}' for m in range(0, 45, 2)))
    out[name] = dict(hist_m=dict(hist_m), hist_s=dict(hist_s), top=top, n_sigma1=sum(v for k, v in hist_s.items() if k >= 1),
                     n_sigma2=sum(v for k, v in hist_s.items() if k >= 2), sigma_pairs={f'{i},{j}': s for (i, j), (m, s) in pairs.items()})
json.dump(out, open(Path.home()/'xs-campaigns/2026-11-07-sprint/qbound/pair_sigma.json', 'w'))
