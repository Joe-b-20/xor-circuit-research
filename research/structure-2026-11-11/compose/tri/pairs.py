"""CHECK: Theorem 9.2 families F_j and pair counts P(j,j+1) (ancestors of the pair nonzero on block j or j+1).
usage: python3 pairs.py FILE LINE [verbose]"""
import sys
from show_tri import load, circuit, desc, mc
fn, ln = sys.argv[1], int(sys.argv[2]); g = load(fn, ln); vals, anc, outn = circuit(g)
B = mc.BLOCKMASK
W = range(32, 32 + len(g))
A = lambda j: set(w for w in W if j in anc.get(w, ()))
F = {j: set(w for w in A(j) if vals[w] & B[j]) for j in range(8)}
F[3] |= set(w for w in A(3) if vals[w] & B[2] and vals[w] & B[7])
print(fn, ln, "F sizes", [len(F[j]) for j in range(8)], "union", len(set().union(*F.values())))
for j in range(1, 7):
    P = set(w for w in A(j) | A(j + 1) if vals[w] & (B[j] | B[j + 1]))
    print(" P(%d,%d)=%d" % (j, j + 1, len(P)), end="")
print()
if len(sys.argv) > 3:
    P = set(w for w in A(1) | A(2) if vals[w] & (B[1] | B[2]))
    for w in sorted(P):
        tag = ("F1 " if w in F[1] else "   ") + ("F2 " if w in F[2] else "   ")
        print("  g%d %s[%s] %s s%s" % (w, tag, desc(vals[w]), outn.get(w, ""), "".join(map(str, sorted(anc[w])))))
