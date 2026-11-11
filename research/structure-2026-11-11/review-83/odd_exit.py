"""For the two odd hunt records: is the exit value a sum of two earlier signals supported inside {3,7}?"""
import glob, json, os
import families as F

for f in sorted(glob.glob(os.path.join(F.HUNT, "runs/A/workers/free-02/records/g88-d[78]-*.json"))):
    if f.endswith(".verification.json"):
        continue
    gates = [tuple(g) for g in json.load(open(f))["gates"]]
    r = F.analyse(gates)
    if r is None or r["mono"] or any(c[1] for c in r["canc"]):
        continue
    vals = [1 << i for i in range(32)]
    for a, b in gates:
        vals.append(vals[a] ^ vals[b])
    for g, cross, C, u, tris in r["canc"]:
        target = vals[g]
        earlier = [vals[x] for x in range(g) if F.supp(vals[x]) <= F.supp(target)]
        es = set(earlier)
        pair = [(hex(x), hex(x ^ target)) for x in earlier if (x ^ target) in es and x < (x ^ target)]
        print(os.path.basename(f), "gate", g, "value", hex(target), "earlier signals inside its support:", len(earlier),
              "pairs summing to it:", pair[:5])
