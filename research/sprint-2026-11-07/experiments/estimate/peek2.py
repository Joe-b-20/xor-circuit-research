import json, collections
H = "/home/joebachir20/xs-campaigns/2026-11-07-sprint/hunt/"
s = json.load(open(H + "plateaus.json"))
for k, v in s["plateaus"].items():
    if v["kind"] != "product":
        print(k, v["plateau"]["meta"], v["depth"])
        break
for k in ("pc0c31eb7788d5c66", "p5d74d61aab10fa15"):
    print(k, s["plateaus"][k]["plateau"]["meta"])
L = json.load(open("/home/joebachir20/xs-campaigns/2026-11-07-sprint/estimate/landings.json"))
g = collections.Counter()
for r in L["rows"]:
    if r["kind"] != "product":
        g[tuple(r["chain_ids"])] += 1
print("non-product keys per chain:", g)
sig = json.load(open(H + "sigs2.json"))
print(len(sig), next(iter(sig.items())))
