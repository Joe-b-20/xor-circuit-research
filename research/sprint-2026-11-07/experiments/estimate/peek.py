import json, collections
H = "/home/joebachir20/xs-campaigns/2026-11-07-sprint/hunt/"
s = json.load(open(H + "plateaus.json"))
print(s.keys())
P = s["plateaus"]; S = s["states"]
print(len(P), len(S), collections.Counter(repr(v) if not v else "key" for v in S.values()))
k = next(iter(P)); print(k, {a: (b if a != "plateau" else list(b.keys())) for a, b in P[k].items()})
kinds = collections.Counter((v["kind"], v["first"]["arm"]) for v in P.values()); print(kinds)
for k, v in P.items():
    if v["kind"] != "product":
        print(k, v["kind"], v["size"], v["radices"], v["first"], v["members_seen"], v["arms"],
              {a: (len(b) if isinstance(b, (list, dict)) else b) for a, b in v["plateau"].items() if a != "factors"})
r = json.loads(open(H + "samples.jsonl").readline()); print({a: (b if a != "values" else len(b)) for a, b in r.items()})
print(collections.Counter(v["members_seen"] for v in P.values()))
