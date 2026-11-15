#!/usr/bin/env python3
"""T3: calibrate slp2 on region 2 of a circuit: base = signals of AND level <= 1 + level-2 ANDs,
targets = the level-3 AND operands. python3 slp2test.py CIRCUIT [restarts]"""
import random
import sys
import time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux.hub.common import load, metrics       # noqa: E402
from pairs import and_levels                        # noqa: E402
from slp2 import SLP2                               # noqa: E402

c = load(sys.argv[1]); R = int(sys.argv[2]) if len(sys.argv) > 2 else 5
n = c.n; t = c.tables(); al = and_levels(c); NS = n + len(c.gates)
base = [t[s] for s in range(NS) if al[s] <= 1] + [t[g] for g in range(n, NS) if c.gates[g - n][0] == 8 and al[g] == 2]
tg = sorted({t[x] for g in range(n, NS) if c.gates[g - n][0] == 8 and al[g] == 3 for x in c.gates[g - n][1:]})
print(metrics(c), 'base', len(base), 'targets', len(tg))
for r in range(R):
    t0 = time.time()
    s = SLP2(base, random.Random(r)); s.verbose = True; k = s.run(tg)
    print('restart %d: %d XORs (%.1fs)' % (r, k, time.time() - t0), flush=True)
