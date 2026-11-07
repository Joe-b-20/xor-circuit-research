import json, os, glob
H = os.path.dirname(os.path.abspath(__file__))
st = json.load(open(os.path.join(H, "plateaus.json")))
seen = st["states"]; P = st["plateaus"]
for arm, path in (("A", "samples.jsonl"), ("B", "samples.jsonl"), ("C", "samplesC/samples.jsonl")):
    hs = set()
    for line in open(os.path.join(H, path)):
        r = json.loads(line)
        if r["gates"] == 88 and r["arm"] == arm:
            hs.add(r["hash"])
    recs = glob.glob(os.path.join(H, "runs", arm, "workers", "*", "records", "g88-*.json"))
    done = sum(1 for h in hs if h in seen)
    n_pl = sum(1 for v in P.values() if v["first"]["arm"] == arm)
    seen_by = sum(1 for v in P.values() if arm in v["arms"])
    giants = sum(1 for v in P.values() if v["first"]["arm"] == arm and v["kind"] == "giant")
    big = sum(1 for v in P.values() if v["first"]["arm"] == arm and v["size"] > 100000)
    print(f"{arm}: 88 sample-states {len(hs)}, catalogued {done}, records {len(recs)}; plateaus first {n_pl} (giant {giants}, size>1e5 {big}), seen by arm {seen_by}")
