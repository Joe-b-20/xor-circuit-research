#!/usr/bin/env python3
"""T4: for one search42 solution, rebuild round 0 of auto42 and try many design variants for the
outputs above the cap (cxplan with more parameter values); report per-output Kraft.
    python3 fix42.py FRONT SOLUTION_JSON OUTDIR [NVAR]"""
import sys, json, os
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import auto42 as A  # noqa
from coversearch import bound  # noqa
from polpass import kraft  # noqa
import depthsynth as DS  # noqa
from boolflux import core  # noqa
front, sol, outdir = sys.argv[1], json.loads(sys.argv[2]), Path(sys.argv[3]); outdir.mkdir(parents=True, exist_ok=True)
nvar = int(sys.argv[4]) if len(sys.argv) > 4 else 24
basis = sol['B']; pair = sol.get('pair', '02-13')
pr = [tuple(int(ch) for ch in p) for p in pair.split('-')]
p2 = 'p2 %d %d %d %d' % (pr[0][0], pr[0][1], pr[1][0], pr[1][1])
plans = {k: p2 for k in basis}; alts = {}
os.environ['T4_PERDESIGN'] = '6'
for ks, (sv, ex) in sol['detail'].items():
    k = int(ks)
    if k in basis or sv <= 0: continue
    vs = [v for v in A.cx_variants(front, k, basis, pair, nvar) if A.nprod(v) == 4 - sv]
    if vs: alts[k] = vs; plans[k] = vs[0]
order = list(basis) + [k for k in range(8) if k not in basis]
res = A.try_build(front, plans, order)
sk, b, ol, nA = res
print(json.dumps({'ANDs': nA, 'bound': b, 'outs': ol, 'nalts': {k: len(v) for k, v in alts.items()}}), flush=True)
bad = [k for k in range(8) if ol[k] > 11]
for k in bad:
    _, arr, _ = bound(sk, 8)
    print('out', k, 'kraft', kraft(sk['outputs'][k], arr), flush=True)
    for v in alts.get(k, []):
        p = dict(plans); p[k] = v
        r = A.try_build(front, p, order)
        if r is None: continue
        _, arr2, _ = bound(r[0], 8)
        print('  variant', v, 'outs', r[2], 'kraft', round(kraft(r[0]['outputs'][k], arr2), 4), flush=True)
        if max(r[2]) <= 11:
            plans = p; res = r; break
sk, b, ol, nA = res
if b <= int(os.environ.get("T4_CAP", "11")):
    c = DS.synth(sk); m = c.metrics(A.MODEL)
    f = outdir / ('fix-a%d-gd%d.circ.txt' % (m['A'], m['GD']))
    f.write_text(core.write_ncff(c, A.MODEL, comments=['T4 fix42 plans %s' % plans]))
    (outdir / ('fix-a%d-gd%d.skel.json' % (m['A'], m['GD']))).write_text(json.dumps({'plans': {str(k): v for k, v in plans.items()}, 'ands': [[hex(L), hex(R)] for L, R in sk['ands']], 'outputs': [hex(F) for F in sk['outputs']]}))
    print(json.dumps({'circuit': str(f), 'metrics': [m['A'], m['AD'], m['G'], m['GD']], 'plans': plans}))
else:
    print('no bound-11 variant found')
