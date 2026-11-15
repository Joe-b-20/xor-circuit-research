#!/usr/bin/env python3
"""T3: XOR gates per AND-level region and the region's 'exports' (signals read by a higher region).
    python3 regions.py C1 [C2 ...]"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux.hub.common import load, metrics      # noqa: E402
from pairs import and_levels                        # noqa: E402

for f in sys.argv[1:]:
    c = load(f); n = c.n; al = and_levels(c); NS = n + len(c.gates)
    L = max(al[s] for s in c.outputs)
    cnt = [0] * (L + 1); nots = [0] * (L + 1); ands = [0] * (L + 1)
    exp = [set() for _ in range(L + 1)]
    for g in range(n, NS):
        op, a, b = c.gates[g - n]
        if op == 8:
            ands[al[g]] += 1
            for x in (a, b): exp[al[x]].add(x)
        else:
            if op == 3: nots[al[g]] += 1
            else: cnt[al[g]] += 1
            for x in (a, b):
                if al[x] < al[g]: exp[al[x]].add(x)
    print(Path(f).name[:60], metrics(c), 'XOR per region', cnt, 'NOT', nots, 'ANDs', ands,
          'exports (signals read by ANDs or higher regions)', [len(e) for e in exp])
