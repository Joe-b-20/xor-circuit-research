import json
from collections import Counter
S = "/home/joebachir20/xs-campaigns/2026-11-07-sprint"
P = json.load(open(S + "/bridge/profiles.json"))["results"]
ks = ("x", "y", "h", "q", "z", "s", "F", "E_B", "e1", "types")
bad = Counter(); tags = []
for r in P:
    o = r["orbit"]
    diff = [(j, k) for j in (1, 2, 3) for k in ks if o[j + 2][k] != o[j][k]]
    if diff:
        bad[tuple(sorted({k for j, k in diff}))] += 1
        tags.append((r["tag"], diff, [(p["x"], p["y"], p["s"], p["E_B"], p["e1"]) for p in o]))
print("bridge circuits whose profile is not period 2 from step 1:", len(tags), dict(bad))
for t in tags[:14]:
    print("  ", t)


def two(o, j, G):
    b = o[j]["x"] + o[j + 1]["x"] + 2 * G - 192
    ss = o[j]["s"] + o[j + 1]["s"]
    EB = o[j]["E_B"] + o[j + 1]["E_B"]; LH = o[j]["L_H"] + o[j + 1]["L_H"]
    return ss - b, EB, LH


for j in (1, 2, 3, 4):
    c = Counter(); e = Counter()
    for r in P:
        m, EB, LH = two(r["orbit"], j, r["G"])
        c[m == -(EB + LH)] += 1
        if r["G"] == 88:
            e[EB] += 1
    print("phase pair (%d,%d): margin == -(E_B+L_H):" % (j, j + 1), dict(c), " E_B range over 88s:", min(e), max(e), " margin 0 count:", sum(v for k, v in e.items() if k == 0))
