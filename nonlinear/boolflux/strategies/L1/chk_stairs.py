import json
from collections import defaultdict
from l1_lib import Data, fmt, GOALS
D = Data()
struct = json.load(open(str(__import__("l1_lib").OUT / "struct.json")))
pub = sorted(set(D.published))
print("published A<=29:", [fmt(p) for p in pub if p[0] <= 29])
print("published A=32 AD<=5 front-ish:", [fmt(p) for p in pub if p[0] == 32 and p[1] <= 5][:40])
print("published AD3 A<=35:", [fmt(p) for p in pub if p[1] == 3 and p[0] <= 35])
# staircases min G per GD: seeds (main archive) vs long final, classes of the goals
def stair(ids, A, AD):
    best = {}
    for i in ids:
        m = D.m[i]
        if m[0] <= A and m[1] <= AD:
            best[m[3]] = min(best.get(m[3], 999), m[2])
    out = []; cur = 999
    for gd in sorted(best):
        if best[gd] < cur: cur = best[gd]; out.append((gd, cur))
    return out
for name, A, AD in (("28/4", 28, 4), ("28/5", 28, 5), ("29/4", 29, 4), ("29/5",29,5), ("31/5", 31, 5), ("32/4", 32, 4), ("32/6", 32, 6), ("35/3", 35, 3), ("44/4", 44, 4)):
    s0 = stair(D.inarch["main"], A, AD); s1 = stair(D.inarch["long"], A, AD)
    print(name, "seeds (GD,G):", s0); print(name, "long  (GD,G):", s1)
# the same-stage-1-span share
V = defaultdict(float); N = defaultdict(int)
for (c, i), x in D.val.items():
    V[(struct[i]["s1"], struct[i]["d1"] - 9)] += x["V"]; N[(struct[i]["s1"], struct[i]["d1"] - 9)] += 1
tot = sum(V.values())
for k, v in sorted(V.items(), key=lambda kv: -kv[1]): print("stage-1 span", k[0], "level-1 ANDs", k[1], "front adm", N[k], "V %.0f (%.0f%%)" % (v, 100 * v / tot))
