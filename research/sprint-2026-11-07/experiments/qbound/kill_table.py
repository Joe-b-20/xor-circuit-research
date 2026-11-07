#!/usr/bin/env python3
"""Step 1: how many of the G=75 survivors (1,508 oriented claims; 1,134 LP-feasible local keys) would die
under a hypothetical extra universal row of the form q >= c, q+z >= c, or variants, applied to EVERY phase.

Uses the package's own LP model lp_regen.py (unchanged, imported from lb76/pkg_copy) and simply declares a
local key (h,y,F,q,z,ori) infeasible when it violates the hypothetical row.  LP results are cached across
filters (the LP feasibility of a key does not depend on the filter), so the whole table costs one scan plus
the few extra keys the filters make the search visit.
"""
import json, sys, time
from collections import Counter
from pathlib import Path
PKG = Path.home()/'xs-campaigns/2026-11-07-sprint/lb76/pkg_copy/source/lower_bounds/checks'
sys.path.insert(0, str(PKG))
import lp_regen  # noqa: E402  (package LP model, unchanged)
OUT = Path.home()/'xs-campaigns/2026-11-07-sprint/qbound'
G = int(sys.argv[1]) if len(sys.argv) > 1 else 75

orig = lp_regen.feasible          # lru_cached package function
FILTER = [None]
def filtered(h, y, F, q, z, ori):
    if FILTER[0] is not None and not FILTER[0](h, y, F, q, z, ori):
        return False
    return orig(h, y, F, q, z, ori)
filtered.cache_info = orig.cache_info
lp_regen.feasible = filtered      # lp_regen.first_s looks the name up in the module at call time

keys = json.load(open(Path.home()/'xs-campaigns/2026-11-07-sprint/lb76/g75_keys.json'))
feas_keys = [tuple(k) for k in keys['feasible']]   # (h,y,F,q,z,ori)

def scan(name, filt):
    FILTER[0] = filt
    t0 = time.time()
    states, claims, survivors = lp_regen.run(G)
    surv = [dict(state=list(st), ori=ori, k=k, ell=ell, shortfall=st[10]-(k+ell)) for st, ori, k, ell in survivors]
    nkeys = sum(1 for k in feas_keys if filt is None or filt(*k))
    byori = Counter(s['ori'] for s in surv)
    print(f'{name:28s} survivors {len(surv):5d} (M {byori["M"]:4d}, Mt {byori["Mt"]:4d})  LP-feasible keys left {nkeys:4d}  {time.time()-t0:.0f}s', flush=True)
    return dict(name=name, survivors=len(surv), byori=dict(byori), keys_left=nkeys,
                shortfall=dict(Counter(s['shortfall'] for s in surv)), survivor_list=surv)

results = []
results.append(scan('baseline (no extra row)', None))
for c in range(1, 9):
    results.append(scan(f'q >= {c}', (lambda c: lambda h, y, F, q, z, ori: q >= c)(c)))
for c in range(1, 13):
    results.append(scan(f'q + z >= {c}', (lambda c: lambda h, y, F, q, z, ori: q + z >= c)(c)))
for c in range(1, 8):
    results.append(scan(f'q >= {c} (Mt phases only)', (lambda c: lambda h, y, F, q, z, ori: ori == 'M' or q >= c)(c)))
    results.append(scan(f'q >= {c} (M phases only)', (lambda c: lambda h, y, F, q, z, ori: ori == 'Mt' or q >= c)(c)))
# a few shape variants: lower bounds on q growing with y or h (these are the shapes a counting proof would give)
for c in (0, 1, 2, 3, 4):
    results.append(scan(f'q >= y - {c}'.replace('- 0', '').strip(), (lambda c: lambda h, y, F, q, z, ori: q >= y - c)(c)))
for c in (0, 1, 2, 3):
    results.append(scan(f'q + z >= y + {c}', (lambda c: lambda h, y, F, q, z, ori: q + z >= y + c)(c)))
for c in (1, 2, 3, 4):
    results.append(scan(f'2q + z >= {c}', (lambda c: lambda h, y, F, q, z, ori: 2*q + z >= c)(c)))
    results.append(scan(f'q + 2z >= {c}', (lambda c: lambda h, y, F, q, z, ori: q + 2*z >= c)(c)))
json.dump(results, open(OUT/f'kill_table_g{G}.json', 'w'), indent=1)
print('LP keys evaluated in total:', orig.cache_info().currsize)
