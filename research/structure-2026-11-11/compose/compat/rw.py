"""CHECK: per block k, min over sample of R = n - waste and of waste (kste every STRIDE-th + recorded)."""
import os, re, sys
from clib import KSTE, check, cut, load
from corpus import wst
stride = int(sys.argv[1])
C = []
for fn in ["circuits_1.txt", "circuits_2.txt", "circuits_3.txt", "circuits_depth5.txt"]:
    ls = [l for l in open(os.path.join(KSTE, fn)) if l.strip()]
    for n in range(0, len(ls), stride):
        g = [(int(a), int(b)) for a, b in re.findall(r"\(\s*(\d+)\s*,\s*(\d+)\s*\)", ls[n])]
        if all(check(g)):
            C.append(("%s:%d" % (fn, n + 1), g))
for s in ["r88", "r89", "r97"]:
    C.append((s, load(s)))
for k in range(8):
    data = []
    for name, g in C:
        vals, kind, labels = cut(g, k)
        w = wst(g, vals, k)
        data.append((len(g) - w, w, name, len(g)))
    mr = min(data); mw = min(data, key=lambda d: d[1])
    print("k=%d: min R %d (%s, n %d, w %d) | min w %d (%s, R %d) | sum %d" % (k, mr[0], mr[2], mr[3], mr[1], mw[1], mw[2], mw[0], mr[0] + mw[1]))
