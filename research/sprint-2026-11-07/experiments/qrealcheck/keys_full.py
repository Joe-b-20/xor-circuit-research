#!/usr/bin/env python3
"""qrealcheck: the complete set of LP-feasible keys touched by the final scan (not only the 1,134 baseline keys),
and the load-bearing keys (feasible at s = k on the even phase / s = ell on the odd phase of a surviving claim)."""
import sys, json
from collections import Counter
from pathlib import Path
sys.argv = ['keys_full']
import lp_qrc, lp_regen
V = 'GstarN1HUBDARK'; lp_qrc.VARIANT[0] = V
ALL = set(); FEAS = set()
from functools import lru_cache
@lru_cache(None)
def rec(h, y, F, q, z, ori):
    key = (h, y, F, q, z, ori); r = lp_qrc.feasible(*key); ALL.add(key)
    if r: FEAS.add(key)
    return r
lp_regen.feasible = rec
states, claims, survivors = lp_regen.run(75)
base = {tuple(k) for k in json.load(open(Path.home()/'xs-campaigns/2026-11-07-sprint/lb76/g75_keys.json'))['feasible']}
lb = set()
for st, ori, k, ell in survivors:
    a, b, Y, Vv, he, ho, le, lo, Se, So, budget = st; other = 'Mt' if ori == 'M' else 'M'
    for q in range(k + 1):
        if rec(he, Y, Vv, q, k - q, ori): lb.add((he, Y, Vv, q, k - q, ori))
    for q in range(ell + 1):
        if rec(ho, Vv, Y, q, ell - q, other): lb.add((ho, Vv, Y, q, ell - q, other))
print(f'{V}: survivors {len(survivors)}; keys touched {len(ALL)}, LP-feasible {len(FEAS)} (of which in the baseline 1,134 list: {len(FEAS & base)});')
print('  all feasible keys by q', sorted(Counter(k[3] for k in FEAS).items()), 'by ori', dict(Counter(k[5] for k in FEAS)))
print(f'  load-bearing keys {len(lb)} (in baseline list: {len(lb & base)}); by q', sorted(Counter(k[3] for k in lb).items()), 'by ori', dict(Counter(k[5] for k in lb)))
print('  load-bearing keys by z', sorted(Counter(k[4] for k in lb).items()))
for t in [(13, 4, 4, 4, 1, 'M'), (12, 4, 4, 5, 1, 'Mt'), (11, 5, 5, 5, 0, 'Mt'), (19, 0, 0, 1, 5, 'Mt'), (18, 1, 1, 1, 4, 'Mt')]:
    print('  ', t, 'feasible', t in FEAS, 'load-bearing', t in lb)
print('  load-bearing q<=3:', sorted(k for k in lb if k[3] <= 3))
json.dump({'feasible': sorted(FEAS), 'load_bearing': sorted(lb)}, open(Path.home()/'xs-campaigns/2026-11-07-sprint/qrealcheck/keys_full.json', 'w'))
