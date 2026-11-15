#!/usr/bin/env python3
"""Positive controls for wres: (1) inject a redundant 3-gate XOR detour into a front circuit and check that
windows recover the gate count; (2) Synth on a known function (full adder: 5 gates, 1... ) sanity.

    test_wres.py CAMPAIGN SEED SECONDS
"""
import random, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(next(p for p in HERE.parents if (p / 'boolflux' / 'core.py').exists()))); sys.path.insert(0, str(HERE))
from boolflux.core import Circuit                 # noqa: E402
from boolflux.hub.archive import Archive          # noqa: E402
from boolflux.hub.common import metrics           # noqa: E402
import wres as R                                   # noqa: E402
import op_wres as O                                # noqa: E402

camp, seed, secs = sys.argv[1], int(sys.argv[2]), float(sys.argv[3])
rng = random.Random(seed)

# (2) full adder sum/carry over 3 inputs: XAG optimum is 4 gates incl. 1 AND (s = a^b^c, c = ((a^b)&(a^c))^a ... )
k = 3; P = 8
vin = [sum(((t >> (2 - b)) & 1) << t for t in range(8)) for b in range(3)]
sm = vin[0] ^ vin[1] ^ vin[2]; cy = (vin[0] & vin[1]) | (vin[0] & vin[2]) | (vin[1] & vin[2])
okp = [0] * 4
for t in range(8):
    v = ((sm >> t) & 1) | (((cy >> t) & 1) << 1)
    okp[v] |= 1 << t
for r, amax in ((3, 1), (4, 1), (5, 2)):
    sy = R.Synth(k, P, vin, okp, [0, 0, 0], [0, 0, 0], [9, 9], [9, 9], r, amax)
    out = sy.run(100000); sy.close()
    print('full adder r=%d amax=%d:' % (r, amax), out[0], out[1:] if out[0] == 'sat' else '')

# (1) redundancy injection
ar = Archive(camp)
ids = ar.front_ids()
ok = 0; tot = 0
for trial in range(6):
    i = rng.choice(ids); c = ar.circuit(i); n = c.n
    m0 = metrics(c)
    xs = [j for j, g in enumerate(c.gates) if g[0] == 6]
    j = rng.choice(xs); op, a, b = c.gates[j]
    d = rng.randrange(0, n + j)
    while d in (a, b): d = rng.randrange(0, n + j)
    # gates: ... j-1, then t1=a^d, t2=t1^b, t3=t2^d replaces gate j
    g = list(c.gates[:j]) + [(6, a, d), (6, n + j, b), (6, n + j + 1, d)]
    sh = lambda s: s if s < n + j else s + 2
    for (op2, x, y) in c.gates[j + 1:]: g.append((op2, sh(x), sh(y)))
    c2 = Circuit(n, c.m, g, [sh(o) for o in c.outputs]).live()
    assert c2.output_tables() == c.output_tables()
    m2 = metrics(c2)
    caps = {'A': m2[0], 'AD': m2[1], 'GD': m2[3]}
    t0 = time.time()
    cands, info = O.run(c2, caps, O.DEFAULT_OBJECTIVE.split(','), secs, rng, sideways=0.0)
    fk = info['final_key']
    tot += 1; ok += fk[2] <= m0[2]
    print('inject', i, 'orig', m0, 'injected', m2, '-> final', fk, 'windows', info['windows'], 'stats', info['stats'])
print('recovered %d / %d' % (ok, tot))
