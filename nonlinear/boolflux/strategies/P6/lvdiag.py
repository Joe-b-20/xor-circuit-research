#!/usr/bin/env python3
"""P6: actual levels vs Huffman arrivals for every AND (shows where a build loses depth)."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core
from skelan import anatomy
import botbasis as BB
c = BB.load(sys.argv[1]); n = c.n
sk, arr, alv = anatomy(c)
lv = [0] * n; k = 0; rows = []
for j, (op, a, b) in enumerate(c.gates):
    lv.append(1 + max(lv[a], lv[b]))
    if op == core.OPS['AND']:
        p = 1 + n + k; rows.append((k, alv[p], arr[p], lv[-1], lv[a], lv[b])); k += 1
for r in rows:
    flag = ' <-- late' if r[3] > r[2] else ''
    print('AND%2d lvl%d huff %2d actual %2d (ops %d,%d)%s' % (r + (flag,)))
print('outputs actual', [lv[o] for o in c.outputs])
