#!/usr/bin/env python3
"""Light extraction for the report: H2 witnesses with X = 0, survivor/key tables of the final scans, status of
qreal's q <= 3 keys, even/odd-side key usage.  usage: python3 extract.py VARIANT [VARIANT2 ...]"""
import json, sys
from collections import Counter
from pathlib import Path
OUT = Path.home()/'xs-campaigns/2026-11-07-sprint/qhub'
QREAL = Path.home()/'xs-campaigns/2026-11-07-sprint/qreal'

for ori in ('M', 'Mt'):
    d = json.load(open(OUT/f'hub2_{ori}.json'))
    for r in ('0', '1', '2'):
        t = d['table'][r]
        print(f'{ori} r={r}: K={t["K"]} K_sigma={t["K_sigma"]}; sigma0 witnesses (first 3): {t["witnesses_sigma0"][:3]}')
        # how many hub values attain 3 - r with X = 0
        n0 = sum(1 for h, rec in d['cap'][r].items() if rec['sig']['0'] == 3 - int(r))
        print(f'{ori} r={r}: hub values attaining 3-r with X <= 0: {n0}; with any X: {sum(1 for h, rec in d["cap"][r].items() if rec["c13"] == 3 - int(r))}')

base = json.load(open(QREAL/'scan_GstarN1HUBDARKMFM_q0_g75.json'))
base_keys = {tuple(k) for k in base['keys_still_feasible']}
q3 = [k for k in base_keys if k[3] <= 3]
for variant in sys.argv[1:]:
    d = json.load(open(OUT/f'scan_{variant}_q0_g75.json'))
    keys = [tuple(k) for k in d['keys_still_feasible']]; ks = set(keys)
    surv = d['survivors']
    print(f'\n=== {variant}: claims {len(surv)} (M {sum(1 for x in surv if x["ori"]=="M")}, Mt {len(surv)-sum(1 for x in surv if x["ori"]=="M")}); keys {len(keys)}')
    print('  keys by (q,z):', sorted(Counter((k[3], k[4]) for k in keys).items()))
    print('  keys by (ori,q):', sorted(Counter((k[5], k[3]) for k in keys).items()))
    print('  keys by h:', sorted(Counter(k[0] for k in keys).items()))
    print('  shortfall:', sorted(Counter(x['shortfall'] for x in surv).items()))
    print('  qreal q<=3 keys still feasible:', sorted(k for k in q3 if k in ks))
    print('  qreal q<=3 keys killed:', sorted(k for k in q3 if k not in ks))
    ev = Counter((x['state'][4], x['state'][2], x['state'][3], x['ori'], x['k']) for x in surv)
    od = Counter((x['state'][5], x['state'][3], x['state'][2], ('Mt' if x['ori'] == 'M' else 'M'), x['ell']) for x in surv)
    print('  even-side (h,y,F,ori,k) most used:', ev.most_common(12))
    print('  odd-side (h,y,F,ori,ell) most used:', od.most_common(12))
    # which keys are load-bearing: a key (h,y,F,q,z,ori) is used by a claim if q+z = k (even) or = ell (odd) and feasible
    used = Counter()
    for x in surv:
        a, b, Y, V, he, ho, le, lo, Se, So, budget = x['state']; ori = x['ori']; oth = 'Mt' if ori == 'M' else 'M'
        for k in keys:
            if k[:3] == (he, Y, V) and k[5] == ori and k[3] + k[4] == x['k']: used[k] += 1
            if k[:3] == (ho, V, Y) and k[5] == oth and k[3] + k[4] == x['ell']: used[k] += 1
    print(f'  load-bearing keys (feasible at the claim\'s k or ell): {len(used)}; by (ori,q): {sorted(Counter((k[5], k[3]) for k in used).items())}')
    print('  most used keys:', used.most_common(15))
    print('  all keys:', sorted(keys))
