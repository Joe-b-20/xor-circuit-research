import os
from collections import Counter
import olib
K = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/kste/external/mixcolumns_xor/circuits_2.txt")
c = Counter(); ex = []
for ln, line in enumerate(open(K), 1):
    if not line.strip(): continue
    g = olib.parse_pairs(line)
    comp, red, _ = olib.check(g, olib.ROWS)
    if comp: continue
    vals = olib.values(g); s = set(vals) if vals else set()
    hit = sum(r in s for r in olib.ROWS)
    c[(len(g), hit)] += 1
    if len(ex) < 3: ex.append((ln, line[:80]))
print(c); print(ex)
