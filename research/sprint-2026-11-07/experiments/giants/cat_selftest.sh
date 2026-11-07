#!/bin/bash
# Self-test of cat_worker.py on a 4-item queue in a scratch CAT_DIR (one process, nice 12):
# a giant-free queue with 2 states already in the catalogue, 1 duplicate id, 1 state needing
# compress (time_limit 120).  Then a second run must skip everything (idempotence).
set -u
G=/home/joebachir20/xs-campaigns/2026-11-07-sprint/giants
T=$G/catalogue_selftest
rm -rf "$T"; mkdir -p "$T/claims" "$T/pl"
cp "$G/catalogue/products.json" "$T/"
python3 - "$T" <<'EOF'
import json, sys
T = sys.argv[1]
H = json.load(open("/home/joebachir20/xs-campaigns/2026-11-07-sprint/hunt/plateaus.json"))["states"]
Q = [json.loads(l) for l in open("/home/joebachir20/xs-campaigns/2026-11-07-sprint/giants/catalogue/queue.jsonl")]
S = [q for q in Q if q["kind"] == "sample"]
known = []
for f in ["/home/joebachir20/xs-campaigns/2026-11-07-sprint/hunt/samples.jsonl"]:
    for line in open(f):
        r = json.loads(line)
        if r["gates"] == 88 and H.get(r["hash"]):
            known.append({"id": r["hash"], "kind": "sample", "arm": r["arm"], "worker": r["worker"], "t": r["t"],
                          "values": r["values"], "time_limit": 120})
        if len(known) == 2:
            break
sys.path.insert(0, "/home/joebachir20/xs-campaigns/2026-11-07-sprint/giants")
import cat_lib as C
K = C.Known(T + "/products.json")
need = next(x for x in S[40:] if C.state_of_values(x["values"]) and not K.member(C.state_of_values(x["values"]))[0])
q = known + [known[0], dict(need, time_limit=120)]
with open(T + "/queue.jsonl", "w") as f:
    for x in q:
        f.write(json.dumps(x) + "\n")
EOF
cd "$G"
CAT_DIR=$T nice -n 12 python3 cat_worker.py 0
CAT_DIR=$T nice -n 12 python3 cat_worker.py 1
cut -c1-260 "$T"/shard_*.jsonl; ls "$T/pl" "$T/claims"
