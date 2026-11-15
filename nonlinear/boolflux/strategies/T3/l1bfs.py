#!/usr/bin/env python3
"""T3: BFS over the equal-G plateau of level-1 product exchanges (l1move.l1_variants with dG <= 0).
    python3 l1bfs.py CIRCUIT MAXNODES OUTDIR"""
import sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core
from boolflux.hub.common import load, metrics, cid
from l1move import l1_variants
c = load(sys.argv[1]); M = int(sys.argv[2]); out = Path(sys.argv[3]); out.mkdir(parents=True, exist_ok=True)
G0 = metrics(c)[2]
seen = {cid(c): c}; frontier = [c]; t0 = time.time(); lower = []
while frontier and len(seen) < M:
    nxt = []
    for x in frontier:
        for v in l1_variants(x):
            if v[0] > G0: continue
            if v[3] in seen: continue
            seen[v[3]] = v[4]; nxt.append(v[4])
            if v[0] < G0: lower.append(v)
            if len(seen) >= M: break
        if len(seen) >= M: break
    frontier = nxt
    print('layer: plateau size %d, frontier %d, lower %d (%.0fs)' % (len(seen), len(nxt), len(lower), time.time() - t0), flush=True)
from collections import Counter
print('GD histogram', sorted(Counter(metrics(x)[3] for x in seen.values()).items()))
for k, x in seen.items():
    m = metrics(x)
    (out / ('a%d-ad%d-g%d-gd%d-%s.bfx' % (m + (k,)))).write_text(core.to_kernel(x))
