import glob, json, os
fs = sorted(glob.glob(os.path.expanduser("~/xs-campaigns/2026-10-31-adopt/runs/adopt/workers/inv-cap5-01/records/g118-d5-*.json")))
print(len(fs), fs[0])
d = json.load(open(fs[0]))
for k, v in d.items():
    print(k, ":", repr(v)[:400])
fs2 = sorted(glob.glob(os.path.expanduser("~/xs-campaigns/2026-11-06-layout/workers/runs/*/workers/*/records/g118-d5-*.json")))
print(len(fs2), fs2[0])
d = json.load(open(fs2[0]))
print((d.get("metadata") or {}).get("target"), d.get("gateCount"), d.get("depth"))
