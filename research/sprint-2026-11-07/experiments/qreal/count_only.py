import sys, time, itertools
sys.path.insert(0, ".")
from fullsets2 import setup, Basis
from collections import Counter
ori = sys.argv[1]; cap = int(sys.argv[2])
B, trip, fulls, line, supp = setup(ori)
N = len(fulls); count = Counter(); nodes = [0]; t0 = time.time()
def rec(start, bs, m):
    nodes[0] += 1
    if nodes[0] > cap: raise SystemExit(f"{ori}: CAPPED at {cap} nodes; partial counts {dict(sorted(count.items()))}; {time.time()-t0:.0f}s")
    for i in range(start, N):
        t = bs.copy()
        if t.add(line[fulls[i]][0]) and t.add(line[fulls[i]][1]):
            count[m + 1] += 1; rec(i + 1, t, m + 1)
rec(0, Basis(), 0)
print(f"{ori}: COMPLETE: independent sets by size {dict(sorted(count.items()))}; nodes {nodes[0]}; {time.time()-t0:.0f}s")
