"""c0b_probe.py: formats of the pinned-completion outputs (read-only), and pes_lib search caps."""
import glob, json, os, sys
HOME = os.path.expanduser("~")

def desc(r):
    if isinstance(r, dict):
        return {k: (v if not isinstance(v, (list, dict)) else type(v).__name__ + str(len(v))) for k, v in r.items()}
    return type(r).__name__ + str(len(r))

p = f"{HOME}/xs-campaigns/2026-11-02-why/foundations/out/a-pin-s1.jsonl"
lines = open(p).read().splitlines()
print("a-pin-s1.jsonl lines", len(lines))
for l in lines[:2] + lines[-2:]:
    r = json.loads(l); print("  ", desc(r))
    for k in ("circuit", "gates", "values", "helpers", "best"):
        if k in r: print("     ", k, str(r[k])[:150])

for d in ["2026-11-03-12h/foundation/run", "2026-11-04-12h/foundation2/run", "2026-11-03-waits/repair/run"]:
    full = f"{HOME}/xs-campaigns/{d}"
    print("DIR", d, sorted(os.listdir(full))[:20])
    runs = sorted(glob.glob(full + "/runs/*"))
    print("  runs:", len(runs), [os.path.basename(x) for x in runs[:8]])
    for x in [r for r in runs if os.path.isdir(r)][:1]:
        ents = sorted(os.listdir(x)); print("   ", os.path.basename(x), ents[:20])
        for e in ents:
            if e.endswith(".json"):
                try:
                    r = json.load(open(os.path.join(x, e))); print("      ", e, desc(r))
                except Exception as ex:
                    print("      ", e, "ERR", ex)
    hits = full + "/hits.jsonl"
    if os.path.exists(hits):
        hl = open(hits).read().splitlines(); print("  hits.jsonl", len(hl))
        if hl:
            r = json.loads(hl[0]); print("    ", desc(r))

# every json under those three + foundations/out that has gateCount 90 and depth 4 and 32 inputs
cnt = 0
for d in ["2026-11-02-why/foundations", "2026-11-03-12h/foundation", "2026-11-04-12h/foundation2", "2026-11-03-waits/repair"]:
    full = f"{HOME}/xs-campaigns/{d}"
    for f in glob.glob(full + "/**/*.json", recursive=True):
        try:
            r = json.load(open(f))
        except Exception:
            continue
        if isinstance(r, dict) and r.get("gateCount") == 90 and r.get("depth") == 4:
            cnt += 1
            if cnt <= 5: print("G90 json:", f.replace(HOME, "~"), desc(r))
print("json files with gateCount 90 depth 4:", cnt)

sys.path.insert(0, f"{HOME}/xs-campaigns/2026-11-05-exit/pes")
from pes_lib import make_space
for cap in (4, 5, None):
    sp = make_space("mc", cap)
    print("make_space cap_real", cap, "-> search cap", sp.cap, "shifts", sp.shifts)
