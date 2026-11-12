"""CHECK (reviewer's own code): P(1,2) = gates that are ancestors of an output of sheet 1 or 2 (output bit
position 1 or 2) and nonzero on block 1 or 2. Restrict blocks 3..7 to zero; count distinct restricted values
among P(1,2) that are not free (block 0 only / zero) and not inputs. Lists {2,7} gates in P(1,2).
usage: python3 p12.py KSTEFILE LINE"""
import os, re, sys
from mycheck import rows
fn, ln = sys.argv[1], int(sys.argv[2])
KSTE = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/kste/external/mixcolumns_xor")
ls = [l for l in open(os.path.join(KSTE, fn)) if l.strip()]
g = [(int(a), int(b)) for a, b in re.findall(r"\(\s*(\d+)\s*,\s*(\d+)\s*\)", ls[ln - 1])]
v = [1 << i for i in range(32)]
for a, b in g: v.append(v[a] ^ v[b])
R = rows()
assert all(r in set(v[32:]) for r in R) and len(set(v)) == len(v)
bm = lambda k: sum(1 << (8 * c + k) for c in range(4))
outs = {v.index(R[i * 8 + t]) for i in range(4) for t in (1, 2)}
anc, st = set(), list(outs)
while st:
    s = st.pop()
    if s < 32 or s in anc: continue
    anc.add(s); st.extend(g[s - 32])
B12 = bm(1) | bm(2); keep = bm(0) | B12
P = sorted(w for w in anc if v[w] & B12)
inputs = {1 << i for i in range(32)}
new = {v[w] & keep for w in P} - inputs
new = {x for x in new if x & B12}
print("n=%d |P(1,2)|=%d distinct new restricted values=%d" % (len(g), len(P), len(new)))
for w in P:
    if v[w] & ~(bm(2) | bm(7)) == 0 and v[w] & bm(7) and v[w] & bm(2):
        a, b = g[w - 32]
        print("  {2,7} gate g%d operands g%d (blocks %s) g%d (blocks %s)" % (w, a, [k for k in range(8) if v[a] & bm(k)], b, [k for k in range(8) if v[b] & bm(k)]))
