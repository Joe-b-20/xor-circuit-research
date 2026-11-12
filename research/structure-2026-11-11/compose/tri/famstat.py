"""CHECK: over every STRIDE-th kste circuit (own line numbers): P(1,2), family overlaps, unfamilied gates
(with their supports), sheet-1 targets descending from the block-2-cancelling gate, window-locality.
usage: python3 famstat.py STRIDE"""
import os, sys
from collections import Counter
from show_tri import KSTE, circuit, classes, mc
from scan_tri import FILES
B = mc.BLOCKMASK
def fam(g):
    vals, anc, outn = circuit(g); W = range(32, 32 + len(g))
    A = lambda j: set(w for w in W if j in anc.get(w, ()))
    F = {j: set(w for w in A(j) if vals[w] & B[j]) for j in range(8)}
    F[3] |= set(w for w in A(3) if vals[w] & B[2] and vals[w] & B[7])
    U = set().union(*F.values())
    P12 = len(set(w for w in A(1) | A(2) if vals[w] & (B[1] | B[2])))
    over = sum(len(F[j]) for j in range(8)) - len(U)
    unf = ["".join(map(str, sorted(mc.blocks(vals[w])))) + "/s" + "".join(map(str, sorted(anc[w]))) for w in W if w not in U]
    loc = all(any(mc.blocks(vals[w]) <= S for S in mc.SHEET_SUPPORT) for w in W)
    fl = [len(F[j]) for j in range(8)]
    return vals, anc, outn, P12, over, unf, loc, fl
st = Counter(); stride = int(sys.argv[1])
for fn in FILES:
    for ln, line in enumerate(open(os.path.join(KSTE, fn)), 1):
        if ln % stride: continue
        g = mc.parse_pairs(line); r = mc.analyse(g)
        if r is None: continue
        m = "mono" if r["monotone"] else "non"
        vals, anc, outn, P12, over, unf, loc, fl = fam(g)
        st[(m, "P12=%d" % P12)] += 1
        st[(m, "overlap=%d unfam=%d" % (over, len(unf)))] += 1
        for u in unf: st[(m, "unfam " + u)] += 1
        st[(m, "local" if loc else "nonlocal")] += 1
        st[(m, "F123=%d,%d,%d" % tuple(fl[1:4]))] += 1
        if m == "non":
            cl = classes(g, vals, 2)
            for w, c in cl.items():
                if c != "EXIT": continue
                rd = {}
                for i, (a, b) in enumerate(g):
                    rd.setdefault(a, []).append(32 + i); rd.setdefault(b, []).append(32 + i)
                seen, stack = set(), [w]
                while stack:
                    x = stack.pop()
                    if x in seen: continue
                    seen.add(x); stack.extend(rd.get(x, []))
                tg = sorted(outn[x] for x in seen if x in outn)
                st[(m, "exit feeds %d targets, sheets %s" % (len(tg), "".join(sorted(set(t[3] for t in tg)))))] += 1
for k, v in sorted(st.items()):
    print(v, *k)
