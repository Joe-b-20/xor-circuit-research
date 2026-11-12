"""CHECK: for every STRIDE-th non-monotone kste circuit: the gates repeated when block 7 is zeroed (support,
served sheets), the cancelled block-2 nibble of the exit, the exit value, and the target(s) it feeds.
usage: python3 triple.py STRIDE"""
import os, sys
from collections import Counter
from show_tri import KSTE, circuit, classes, desc, mc, PN, nib
from scan_tri import FILES
B = mc.BLOCKMASK; M = ~B[7] & 0xFFFFFFFF
st = Counter(); stride = int(sys.argv[1])
for fn in FILES:
    for ln, line in enumerate(open(os.path.join(KSTE, fn)), 1):
        if ln % stride: continue
        g = mc.parse_pairs(line); r = mc.analyse(g)
        if r is None or r["monotone"]: continue
        vals, anc, outn = circuit(g); rv = [v & M for v in vals]
        first = {}
        for w in range(32, len(vals)): first.setdefault(rv[w], w)
        units = set(rv[:32])
        P = [w for w in range(32, len(vals)) if (anc.get(w, set()) & {1, 2}) and vals[w] & (B[1] | B[2])]
        rep = [w for w in P if rv[w] == 0 or not (rv[w] & ~B[0]) or rv[w] in units or first[rv[w]] != w]
        for w in rep:
            st["repeat support %s served %s" % ("".join(map(str, sorted(mc.blocks(vals[w])))), "".join(map(str, sorted(anc[w]))))] += 1
        for w, c in classes(g, vals, 2).items():
            if c != "EXIT": continue
            a = g[w - 32][0]
            st["cancelled 2:%s, exit value [%s] type" % (PN[nib(vals[a], 2)], " ".join(
                "%d:%s" % (j, "E" if PN[nib(vals[w], j)][0] == "E" else PN[nib(vals[w], j)][0]) for j in range(8) if nib(vals[w], j)))] += 1
for k, v in sorted(st.items()): print(v, k)
