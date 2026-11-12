"""CHECK: restrict a circuit by setting block 7 inputs to zero; pair (1,2) problem with block 0 free.
Lists P12 gates (ancestors of sheets 1, 2 nonzero on block 1 or 2 in the FULL circuit) with restricted
values, marking restricted values that are free (on block 0 alone, or a unit) or repeat an earlier signal.
usage: python3 restrict7.py FILE LINE"""
import sys
from show_tri import load, circuit, desc, mc
fn, ln = sys.argv[1], int(sys.argv[2]); g = load(fn, ln); vals, anc, outn = circuit(g)
B = mc.BLOCKMASK; M = ~B[7] & 0xFFFFFFFF
rv = [v & M for v in vals]
seen = set(rv[:32]); first = {}
for w in range(32, len(vals)):
    first.setdefault(rv[w], w)
P = [w for w in range(32, len(vals)) if (anc.get(w, set()) & {1, 2}) and vals[w] & (B[1] | B[2])]
new = 0
for w in P:
    r = rv[w]
    if r == 0 or not (r & ~B[0]): tag = "free"
    elif r in seen or first[r] != w: tag = "repeat of %s" % ("input" if r in seen else "g%d" % first[r])
    else: tag = "new"; new += 1
    print("  g%d [%s] -> [%s] %s" % (w, desc(vals[w]), desc(r), tag))
print("P12 =", len(P), " new restricted values =", new)
