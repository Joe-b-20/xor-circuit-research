import sys, os, json, glob, collections
H = os.path.expanduser("~")
S = H + "/xs-campaigns/2026-11-07-sprint"
print("line endings ok")
# hunt arm configs: depth caps
for t in glob.glob(S + "/hunt/*.toml"):
    txt = open(t).read()
    caps = [l for l in txt.splitlines() if "depth" in l or "cap" in l]
    print(os.path.basename(t), caps)
# samples: gates histogram per file
for f in ["hunt/samples.jsonl", "hunt/samplesC/samples.jsonl", "hunt/samplesD/samples.jsonl"]:
    c = collections.Counter()
    arms = collections.Counter()
    for line in open(S + "/" + f):
        d = json.loads(line)
        c[d["gates"]] += 1
        arms[d["arm"]] += 1
    print(f, sorted(c.items()), dict(arms))
# mc87 from89 records
for d in sorted(glob.glob(H + "/xs-campaigns/2026-11-04-mc87/runs/mc87/workers/*")):
    recs = sorted(glob.glob(d + "/records/g8[6789]-*.json"))
    recs = [r for r in recs if not r.endswith("verification.json")]
    print(os.path.basename(d), len(recs), [os.path.basename(r) for r in recs][:6])
# nist circuits
for p in glob.glob(H + "/xor-circuit-research/**/*nist*", recursive=True)[:20]:
    print("nist:", p)
for p in glob.glob(H + "/xs-campaigns/2026-10-30-nist/*")[:30]:
    print("nist-camp:", p)
print(os.listdir(H + "/xor-circuit-research/circuits/aes-mixcolumns/logs"))
# q89check c4 results
for f in ["c3_result.json", "c4_result.json"]:
    p = S + "/q89check/" + f
    if os.path.exists(p):
        d = json.load(open(p))
        print(f, type(d), (list(d.keys())[:20] if isinstance(d, dict) else len(d)))
