#!/usr/bin/env python3
"""T4: is a 'subfield-type' rank-2 form (2-dim space of linear forms inside one GF(16)-line
c*GF(16); orbit sizes 510 and 85 under x -> a x^(2^i)) a member of some 9-product stage-1 cover
of N?  Uses strategies/C/stage1.py encode(9, R1=rep) unchanged.   python3 orbit_sat.py REP_INDEX"""
import sys, json, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'C'))
import stage1, qmc  # noqa
reps = stage1.orbit_reps()
i = int(sys.argv[1])
la, lb, sz = reps[i]
print(json.dumps({'rep': i, 'orbit_size': sz, 'sizes': [r[2] for r in reps]}), flush=True)
f = stage1.encode(9, (la, lb))
ok, model, dt = qmc.solve(f, 'cadical153')
print(json.dumps({'rep': i, 'orbit_size': sz, 'k': 9, 'sat': ok, 'secs': round(dt, 1)}), flush=True)
