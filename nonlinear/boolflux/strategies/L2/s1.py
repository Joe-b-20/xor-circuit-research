"""sp1 join sweep: what AND counts did joins reach, and which pairs reduce A below both parents?"""
import json, os, re, collections
B = os.path.expanduser("~/xs-campaigns/2026-11-13-aes/E/sp1/")
R = []
for i in range(4):
    R += json.load(open(B + "shard%d/splices.json" % i))
print("distinct results", len(R))
def pm(n):
    m = re.search(r"a(\d+)-ad(\d+)-g(\d+)-gd(\d+)", n) or re.search(r"g(\d+)-a(\d+)-gd(\d+)-ad(\d+)", n)
    if not m: return None
    g = list(map(int, m.groups()))
    if n.startswith("aes-sbox") or "-D-" in n and n.startswith("aes-sbox"): return tuple(g)
    return None
import sys
sys.path.insert(0, os.path.expanduser("~/xcr-boolflux/nonlinear/boolflux/strategies/E"))
from common import load, metrics
fl = open(B + "files.list").read().split()
M = {os.path.basename(f): tuple(metrics(load(f))) for f in fl}
print("inputs", len(M), "A histogram of inputs", sorted(collections.Counter(m[0] for m in M.values()).items()))
hA = collections.Counter(r["metrics"][0] for r in R)
print("A histogram of join results", sorted(hA.items()))
red = [r for r in R if r["metrics"][0] < min(M[r["X"]][0], M[r["Y"]][0])]
print("results with A below both parents:", len(red))
c = collections.Counter()
for r in red:
    c[(M[r["X"]][0], M[r["Y"]][0], r["metrics"][0], r["LX"], r["LY"])] += 1
for k, v in sorted(c.items()): print("  A_front %d A_back %d -> A %d  LX %d LY %d : %d" % (k + (v,)))
# lowest A results and joins that involve an A<=29 parent
low = sorted([r for r in R if r["metrics"][0] <= 31], key=lambda r: r["metrics"])
print("A<=31 results:", len(low))
seen = set()
for r in low:
    k = tuple(r["metrics"])
    if k in seen: continue
    seen.add(k)
    print("  ", r["metrics"], "front", r["X"], M[r["X"]], "LX", r["LX"], "back", r["Y"], M[r["Y"]], "LY", r["LY"], "if", r["interface"], "need", r["need"])
    if len(seen) > 40: break
# pairs involving an A28 parent: what comes out
a28 = [r for r in R if M[r["X"]][0] == 28 or M[r["Y"]][0] == 28]
print("joins with an A28 parent:", len(a28), "A hist", sorted(collections.Counter(r["metrics"][0] for r in a28).items()))
mix = [r for r in a28 if not (M[r["X"]][0] == 28 and M[r["Y"]][0] == 28)]
print("  of which mixed (one A28, one not):", len(mix), sorted(collections.Counter(r["metrics"][0] for r in mix).items()))
best = sorted(mix, key=lambda r: r["metrics"])[:8]
for r in best: print("    ", r["metrics"], r["X"], r["LX"], r["Y"], r["LY"])
both = [r for r in a28 if M[r["X"]][0] == 28 and M[r["Y"]][0] == 28 and M[r["X"]][1] != M[r["Y"]][1]]
print("  AD4 x AD5 A28 pairs:", len(both), sorted(collections.Counter(tuple(r["metrics"][:2]) for r in both).items()))
