"""CHECK: corpus version of restrict7.py (every STRIDE-th circuit, own line numbers).
For each circuit: P12, number of new restricted values (block 7 zeroed, block 0 free), and for
non-monotone circuits whether the repeats include the operand of the block-2-cancelling gate that has a
block-7 part. usage: python3 restrict7_stat.py STRIDE"""
import os, sys
from collections import Counter
from show_tri import KSTE, circuit, classes, mc
from scan_tri import FILES
B = mc.BLOCKMASK; M = ~B[7] & 0xFFFFFFFF
st = Counter(); stride = int(sys.argv[1])
for fn in FILES:
    for ln, line in enumerate(open(os.path.join(KSTE, fn)), 1):
        if ln % stride: continue
        g = mc.parse_pairs(line); r = mc.analyse(g)
        if r is None: continue
        m = "mono" if r["monotone"] else "non"
        vals, anc, outn = circuit(g); rv = [v & M for v in vals]
        first = {}
        for w in range(32, len(vals)): first.setdefault(rv[w], w)
        units = set(rv[:32])
        P = [w for w in range(32, len(vals)) if (anc.get(w, set()) & {1, 2}) and vals[w] & (B[1] | B[2])]
        rep = [w for w in P if rv[w] == 0 or not (rv[w] & ~B[0]) or rv[w] in units or first[rv[w]] != w]
        new = len(P) - len(rep)
        st[(m, "P12=%d new=%d repeats=%d" % (len(P), new, len(rep)))] += 1
        if m == "non":
            for w, c in classes(g, vals, 2).items():
                if c != "EXIT": continue
                ops = [x for x in g[w - 32] if vals[x] & B[7] and vals[x] & B[2]]
                tag = "{2,7}-type operand(s) %d; repeated in restriction: %s" % (len(ops), [x in rep for x in ops])
                st[(m, tag)] += 1
for k, v in sorted(st.items()): print(v, *k)
