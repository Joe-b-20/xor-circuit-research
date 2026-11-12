"""CHECK: nibbles of the {2,7} partner (gate repeated under block-7 restriction) and of its readers
in sheet 3; every STRIDE-th non-monotone circuit. usage: python3 partner.py STRIDE"""
import os, sys
from collections import Counter
from show_tri import KSTE, circuit, desc, mc
from scan_tri import FILES
B = mc.BLOCKMASK; M = ~B[7] & 0xFFFFFFFF
st = Counter(); stride = int(sys.argv[1])
for fn in FILES:
    for ln, line in enumerate(open(os.path.join(KSTE, fn)), 1):
        if ln % stride: continue
        g = mc.parse_pairs(line); r = mc.analyse(g)
        if r is None or r["monotone"]: continue
        vals, anc, outn = circuit(g)
        for w in range(32, len(vals)):
            if mc.blocks(vals[w]) == frozenset([2, 7]) and anc.get(w) == {1, 3}:
                a, b = g[w - 32]
                st["partner [%s] = [%s] + [%s]" % (desc(vals[w]), desc(vals[a]), desc(vals[b]))] += 1
for k, v in st.most_common(12): print(v, k)
