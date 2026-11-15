"""Generate 9-product level-1 covers of V_N (N = x^17) from Karatsuba norm formulas in many tower
bases: N = N_{F/K}(x) = c0^2 N(e0) + c1^2 N(e1) + c0 c1 T, c0 c1 by Karatsuba over K/Q/GF(2).
Writes one JSON per distinct junk space W = span(L1) / V_N.  usage: gen_l1.py OUTDIR MAX"""
import json
import random
import sys

import cover1
from h4lib import Circ, Tower, Level, norm, K, Q, F, GF2, pw, mul, _indep
from ad3sat import XT, NT
from h4lib import ONES

out, mx = sys.argv[1], int(sys.argv[2])
rnd = random.Random(7)
seen = set(); n = 0
VNrows = cover1.rowspace([ONES] + XT + [t for t in NT if t])
tries = 0
while n < mx and tries < 20000:
    tries += 1
    kinds = tuple(rnd.choice(('normal', 'poly')) for _ in range(3))
    gens = []
    for i, (sub, fld) in enumerate(((GF2, Q), (Q, K), (K, F))):
        q = len(sub)
        while True:
            t = rnd.choice(fld)
            if t in sub: continue
            if kinds[i] == 'normal' and not _indep(t, pw(t, q), sub): continue
            break
        gens.append(t)
    try:
        T = Tower(kinds, gens)
    except Exception:
        continue
    C = Circ()
    Nb = norm(C, T, C.x, 3)
    assert C.ands == 9
    tabs = C.tab[9:]
    W = cover1.rowspace([cover1.reduce(t, VNrows) for t in tabs])
    key = tuple(sorted(W.values()))
    if key in seen: continue
    seen.add(key)
    ops = []
    for w in range(9, len(C.tab)):
        kd = C.kind[w]
        ops.append(['%x' % C.table(kd[1]), '%x' % C.table(kd[2])])
    json.dump({'kinds': kinds, 'gens': gens, 'l1ops': ops, 'dimW': len(W)},
              open('%s/l1_%03d.json' % (out, n), 'w'))
    n += 1
print('distinct', n, 'tries', tries)
