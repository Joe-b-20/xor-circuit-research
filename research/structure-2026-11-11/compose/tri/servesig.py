"""CHECK: gate counts by served-sheet set and by support, for two circuits side by side.
usage: python3 servesig.py FILE1 LINE1 FILE2 LINE2"""
import sys
from collections import Counter
from show_tri import load, circuit, mc
def sig(fn, ln):
    g = load(fn, ln); vals, anc, _ = circuit(g)
    S = Counter("".join(map(str, sorted(anc.get(32 + i, ())))) for i in range(len(g)))
    P = Counter("".join(map(str, sorted(mc.blocks(vals[32 + i])))) for i in range(len(g)))
    r = mc.analyse(g)
    return S, P, r
a = sig(sys.argv[1], int(sys.argv[2])); b = sig(sys.argv[3], int(sys.argv[4]))
for name, i in (("served", 0), ("support", 1)):
    keys = sorted(set(a[i]) | set(b[i]), key=lambda k: (len(k), k))
    print(name + ":", "  ".join("%s:%d/%d" % (k, a[i][k], b[i][k]) for k in keys if a[i][k] != b[i][k]))
for k in ("charges", "excess", "uncharged", "sum_mu"):
    print(k, a[2][k], b[2][k])
