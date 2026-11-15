import sys, os, json, glob, collections
P = os.path.expanduser("~/xcr-boolflux/nonlinear/boolflux")
sys.path.insert(0, P + "/campaigns"); sys.path.insert(0, os.path.dirname(P)); sys.path.insert(0, os.path.dirname(os.path.dirname(P)))
import aes_check
pub = aes_check.published()
print("published():", len(pub), "distinct tuples", len(set(u for u, n in pub)))
c = collections.Counter(os.path.basename(os.path.dirname(str(n))) if "/" in str(n) else "?" for u, n in pub)
print(c)
print("sample", pub[0])
A = collections.Counter(u[0] for u, n in pub)
print("A hist", sorted(A.items()))
print("A<=31:", sorted(u for u, n in pub if u[0] <= 31))
def leq(u, m): return all(a <= b for a, b in zip(u, m))
# our results: manifest tuples
m = json.load(open(P + "/results/MANIFEST.json"))
ours = set()
for e in m["entries"]:
    if e.get("target") == "aes":
        mt = e["metrics"]; ours.add((mt["A"], mt["AD"], mt["G"], mt["GD"]))
pubt = set(u for u, n in pub)
new = [t for t in ours if not any(leq(u, t) for u in pubt)]
front = [t for t in new if not any(o != t and leq(o, t) for o in ours)]
print("manifest AES tuples", len(ours), "new on pin", len(new), "front", len(front), "manifest count", m["aes_pareto"]["count"])
# goal table at pre-hub time
def best(caps, pool):
    A, AD, GD = caps
    c = [t for t in pool if t[0] <= A and t[1] <= AD and t[3] <= GD]
    return min(c, key=lambda t: t[2]) if c else None
for gd in (13, 14, 15, 16, 17, 18, 19, 20, 21, 29):
    print("GD<=%d pub %s ours(prehub manifest) %s" % (gd, best((99, 99, gd), pubt), best((99, 99, gd), ours)))
for name, caps in (("B 28/4/gd22", (28, 4, 22)), ("C 28/5/gd19", (28, 5, 19)), ("D 32/4/gd19", (32, 4, 19)), ("E 32/6/gd31", (32, 6, 31)), ("F 35/3/gd26", (35, 3, 26)), ("G 44/4/gd11", (44, 4, 11)), ("G' 44/4/gd12", (44, 4, 12)), ("A<=31 any", (31, 99, 99)), ("A<=31 gd<=16", (31, 99, 16)), ("A<=30 gd16", (30, 99, 16))):
    print(name, "pub", best(caps, pubt), "ours-prehub", best(caps, ours))
json.dump({"pub": sorted(pubt), "ours": sorted(ours), "front": sorted(front)}, open(os.path.expanduser("~/xs-campaigns/2026-11-15-study/L2/tuples.json"), "w"))
