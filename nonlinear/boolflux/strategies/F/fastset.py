#!/usr/bin/env python3
"""Which inversion outputs must be one level earlier for 116's bottom to meet cap 14 (track F).
For each subset F of the 9 y-combos used by the products (made one level earlier), check Kraft
at cap D for every output with the unchanged product set; print the minimal feasible subsets."""
import itertools
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2])); sys.path.insert(0, str(HERE))
from boolflux import core   # noqa: E402
from bottom import extract, vec   # noqa: E402

c = core.read_ncff(sys.argv[1]); D = int(sys.argv[2]) if len(sys.argv) > 2 else 14
prods, T, yfull, have, lv = extract(c)
fast = {1, 2, 4, 8, 1 | 4, 2 | 8}
arr = {x: (10 if x in fast else 11) for x in range(1, 16)}
combos = sorted({a for a, b, s in prods})
# output term sets: the unique representation over the 18 independent products
from bottom import Bottom
B = Bottom(T, arr, D, have)
cost, ex, sets = B.evaluate([(a, b) for a, b, s in prods])
names = {1: 'y0', 2: 'y1', 4: 'y2', 8: 'y3', 5: 'y0^y2', 10: 'y1^y3', 3: 'y0^y1', 12: 'y2^y3', 15: 'y0123'}
print('combos used:', [names.get(a, a) for a in combos])
for i, st in enumerate(sets):
    print('S%d terms:' % i, sorted(names.get(a, a) for a, b in st))
found = []
for k in range(0, len(combos) + 1):
    for F in itertools.combinations(combos, k):
        if any(set(f) <= set(F) for f in found): continue
        ok = True
        for st in sets:
            kr = sum(2.0 ** (arr[a] - (1 if a in F else 0) + 1 - D) for a, b in st)
            if kr > 1 + 1e-9: ok = False; break
        if ok:
            found.append(F); print('feasible with earlier:', [names.get(a, a) for a in F])
