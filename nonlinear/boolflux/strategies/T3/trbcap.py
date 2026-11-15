#!/usr/bin/env python3
"""T3: try trb rebuilds of each region kind at a hard cap D below the circuit's GD; report best G.
    python3 trbcap.py FILE D REPS [OUT.bfx]"""
import random, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core
from boolflux.hub import trb_impl
from boolflux.hub.common import load, metrics
c = load(sys.argv[1]); D = int(sys.argv[2]); R = int(sys.argv[3]); rng = random.Random(1)
best = None; stats = {}
for r in range(R):
    kind = rng.choice(['bottom', 'mid', 'top', 'random'])
    cur = c
    for step in range(3):           # short chains
        try:
            nc, info = trb_impl.rebuild(cur, D, kind if step == 0 else rng.choice(['bottom', 'mid', 'top', 'random']), rng)
        except Exception as e:
            stats['err'] = stats.get('err', 0) + 1; break
        m = metrics(nc); cur = nc
        if m[3] <= D:
            stats[kind] = min(stats.get(kind, 999), m[2])
            if best is None or m[2] < best[0]: best = (m[2], nc)
            break
print(metrics(c), 'cap', D, 'best G', best[0] if best else None, stats)
if best and len(sys.argv) > 4: Path(sys.argv[4]).write_text(core.to_kernel(best[1]))
