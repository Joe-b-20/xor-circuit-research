#!/usr/bin/env python3
"""Record every local key (h,y,F,orientation,q,z) that the package's own LP model (lp_regen.py,
unchanged) touches at G=75, and whether the inherited rows (L1)-(L23) prove it infeasible.
The LP-feasible keys are the local systems that a 76 proof built on this machinery must kill
(or render unnecessary by pushing k, ell elsewhere); the infeasible ones are the certificates
the existing generator would emit at G=75.  Also measures cost per LP.
"""
import json, sys, time
from collections import Counter
from pathlib import Path

PKG = Path.home()/'xs-campaigns/2026-11-07-sprint/lb76/pkg_copy/source/lower_bounds/checks'
sys.path.insert(0, str(PKG))
import lp_regen  # noqa: E402

OUT = Path.home()/'xs-campaigns/2026-11-07-sprint/lb76'
G = int(sys.argv[1]) if len(sys.argv) > 1 else 75

orig = lp_regen.feasible
record = {}
def recording(h, y, F, q, z, ori):
    key = (h, y, F, q, z, ori)
    if key not in record:
        t = time.perf_counter()
        r = orig(h, y, F, q, z, ori)
        record[key] = (r, time.perf_counter()-t)
    return record[key][0]
recording.cache_info = orig.cache_info
lp_regen.feasible = recording

states, claims, survivors = lp_regen.run(G)
feas = [k for k, (r, _) in record.items() if r]
infeas = [k for k, (r, _) in record.items() if not r and not lp_regen.direct(k[5], k[3], k[4])
          and 2*k[0]+k[1]+k[4]+k[3]*(k[3]-1)//2 >= 32]
direct = [k for k, (r, _) in record.items() if not r and lp_regen.direct(k[5], k[3], k[4])]
times = [t for (r, t) in record.values() if t > 0]
print(f'G={G}: keys touched {len(record)}, LP-feasible {len(feas)}, LP-infeasible (certificate needed) {len(infeas)}, direct exclusions {len(direct)}')
print(f'mean seconds per key {sum(times)/len(times):.4f}, max {max(times):.3f}, total {sum(times):.1f}')
print('feasible keys by orientation:', Counter(k[5] for k in feas))
print('feasible keys by s=q+z:', sorted(Counter(k[3]+k[4] for k in feas).items()))
print('feasible keys by q:', sorted(Counter(k[3] for k in feas).items()))
print('feasible keys by z:', sorted(Counter(k[4] for k in feas).items()))
print('feasible keys by y:', sorted(Counter(k[1] for k in feas).items()))
print('feasible keys by h:', sorted(Counter(k[0] for k in feas).items()))
print('feasible keys by F:', sorted(Counter(k[2] for k in feas).items()))
# which feasible keys are actually load-bearing: referenced by a surviving claim at s = k (even) or s = ell (odd)
load = Counter()
for st, ori, k, ell in survivors:
    a, b, Y, V, he, ho, le, lo, Se, So, budget = st
    other = 'Mt' if ori == 'M' else 'M'
    for q in range(k+1):
        key = (he, Y, V, q, k-q, ori)
        if record.get(key, (False,))[0]: load[key] += 1
    for q in range(ell+1):
        key = (ho, V, Y, q, ell-q, other)
        if record.get(key, (False,))[0]: load[key] += 1
print(f'distinct feasible keys that block a surviving claim: {len(load)}')
print('most-referenced blocking keys:', load.most_common(12))
json.dump({'G': G, 'keys_touched': len(record), 'feasible': sorted(feas, key=str), 'infeasible': sorted(infeas, key=str),
           'direct': sorted(direct, key=str), 'blocking': {str(k): v for k, v in load.items()},
           'mean_seconds_per_key': sum(times)/len(times)}, open(OUT/f'g{G}_keys.json', 'w'), indent=1, default=str)
