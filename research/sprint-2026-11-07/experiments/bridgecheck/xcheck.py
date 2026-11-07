import json, sys
from collections import Counter
S = "/home/joebachir20/xs-campaigns/2026-11-07-sprint"
P = json.load(open(S + "/bridge/profiles.json"))["results"]
R = json.load(open(S + "/bridgecheck/recheck.json"))["results"]


# 1. bridge data: tail margin over all records, as tail.py defines it
def tail(r):
    o = r["orbit"]; s1, s2 = o[1], o[2]; ev, od = (s1, s2) if s1["y"] >= s2["y"] else (s2, s1)
    G = r["G"]; b = ev["x"] + od["x"] + 2 * G - 192; ss = ev["s"] + od["s"]; EB = s1["E_B"] + s2["E_B"]; LH = s1["L_H"] + s2["L_H"]
    return ss - b, EB, LH, o[3]["e1"] - o[1]["e1"]


for name, sel in (("sampled", [r for r in P if r["tag"].startswith("sample")]), ("kste", [r for r in P if r["tag"].startswith("kste")]), ("repo", [r for r in P if r["tag"].startswith("repo")])):
    t = [tail(r) for r in sel]
    print(name, len(sel), "margin", sorted(Counter(x[0] for x in t).items()), "EB", sorted(Counter(x[1] for x in t).items()), "LH", Counter(x[2] for x in t), "drift13", Counter(x[3] for x in t))


def per(r, ks, j0):
    o = r["orbit"]; return all(all(o[j + 2][k] == o[j][k] for k in ks) for j in range(j0, 4))


ks = ("x", "y", "h", "q", "z", "F", "E_B", "e1", "types")
print("bridge 303: profile period-2 from step1:", Counter(per(r, ks, 1) for r in P), " from step0:", Counter(per(r, ks, 0) for r in P))
# 2. repo circuits in bridge: reconstruction vs true gate list
for r in P:
    if r["tag"].startswith("repo"):
        a = r["orbit"][0]; b = r["true_orbit"][0]
        print(r["tag"], "bridge recon C (x,y,q,z,F,E_B)=", (a["x"], a["y"], a["q"], a["z"], a["F"], a["E_B"]), "true=", (b["x"], b["y"], b["q"], b["z"], b["F"], b["E_B"]), "recon info", r["recon"],
              "variants (x,y) set:", sorted({(v.get("x"), v.get("y")) for v in r["variants"] if "x" in v}))
# 3. weight-2 represented failures in my data
for r in R:
    for o in r["orbit"]:
        if o["w2"] != o["w2_rep"]:
            print("w2 not all represented:", r["tag"], "step", o["step"], o["ori"], "w2", o["w2"], "rep", o["w2_rep"])
bad = Counter()
for r in P:
    for o in r["orbit"]:
        if o["w2"] != o["w2_rep"]:
            bad[(r["tag"].split(":")[0], o["step"])] += 1
print("bridge 303 phases with w2 != w2_rep:", dict(bad))
# 4. the circuits where my base differs: tail margins mine vs bridge
mine = {r["tag"]: r for r in R}
for t in ("sample:A:02029264062898f0", "kste:1", "repo:xor89-depth4", "repo:xor97-depth3", "sample:D:e6d1bfdc803f8960"):
    r = [x for x in P if x["tag"] == t][0]
    print(t, "bridge tail (margin,EB,LH,drift)", tail(r), "| mine", tail(mine[t]), "| mine alternatives raw margins", [a["raw_margin"] for a in mine[t]["alternatives"]][:16])
# 5. mobility of weight-2 values on my 30 hunt circuits
try:
    sys.path.insert(0, "/home/joebachir20/xs-campaigns/2026-11-05-exit/pes")
    from pes_lib import make_space, fan
    sp = make_space("mc", None); pc = lambda v: bin(v).count("1")
    hunt = {}
    for f in ("/hunt/samples.jsonl", "/hunt/samplesD/samples.jsonl"):
        for line in open(S + f):
            d = json.loads(line); hunt[d["hash"]] = d
    res = []
    for r in R:
        if not r["tag"].startswith("sample"):
            continue
        vals = hunt[r["tag"].split(":")[2]]["values"]
        Sh = frozenset(v for v in vals if v not in sp.tset)
        g, dep, neutral, downs, binds = fan(sp, Sh)
        w2 = {v for v in Sh if pc(v) == 2}; gone = set()
        for out_set, add_set, hk, dd in neutral:
            gone |= set(out_set)
        res.append((g, len(neutral), len(downs), len(w2), len(w2 & gone), len(Sh & gone)))
    print("mobility (engine gates, neutral, downs, w2, w2 mobile, mobile total):", res)
    print("w2 mobile hist:", Counter(x[4] for x in res), "improving moves:", Counter(x[2] for x in res))
except Exception as ex:
    print("mobility not run:", repr(ex))
