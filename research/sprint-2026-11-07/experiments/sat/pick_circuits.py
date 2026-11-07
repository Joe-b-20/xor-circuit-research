"""Pick structurally different 88 circuits from the hunt samples: distinct plateau cores
(core = values no neutral remove1 move touches, via pes_lib.fan).  Writes circuits.json with
for each pick: id, depth, core size, mobile part (helpers not in the core)."""
import sys, os, json, random, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.expanduser("~/xs-campaigns/2026-11-05-exit/pes"))
import sat87
import pes_lib

sp = pes_lib.make_space("mc", None)
rng = random.Random(7)
picks = []
seen_cores = []
sources = []
for which, path in (("sampleA", os.path.join(sat87.SPRINT, "hunt/samples.jsonl")),
                    ("sampleC", os.path.join(sat87.SPRINT, "hunt/samplesC/samples.jsonl"))):
    lines = open(path).read().splitlines()
    for i, line in enumerate(lines):
        d = json.loads(line)
        if d.get("gates") == 88:
            sources.append((which, i, d))
print("88 samples:", len(sources))
rng.shuffle(sources)
# prefer different workers/arms
byworker = {}
for s in sources:
    byworker.setdefault((s[2].get("arm"), s[2].get("worker")), []).append(s)
print("workers:", len(byworker))
cands = []
keys = list(byworker)
rng.shuffle(keys)
for kkey in keys:
    cands.append(byworker[kkey][0])
t0 = time.time()
for which, i, d in cands:
    if len(picks) >= 6 or time.time() - t0 > 400:
        break
    vals = d["values"]
    helpers = frozenset(v for v in vals if v not in sat87.TSET)
    try:
        g, dep, neutral, downs, binds = pes_lib.fan(sp, helpers)
    except Exception as e:
        print("fan failed", which, i, e); continue
    touched = set()
    for R, A, hk, dd in neutral:
        touched |= set(R)
    core = helpers - touched
    if downs:
        print("!!! DOWN MOVE at", which, i, downs)
    key = frozenset(min(sat87.rot(v, s) for s in range(4)) for v in core)
    # structurally different: core overlap small
    if any(len(key & c) > 0.6 * len(key) for c in seen_cores):
        continue
    seen_cores.append(key)
    picks.append({"id": "%s:%d" % (which, i), "depth": dep, "gates": g, "arm": d.get("arm"),
                  "worker": d.get("worker"), "core_size": len(core), "n_neutral": len(neutral),
                  "mobile": sorted(helpers - core), "core": sorted(core)})
    print(picks[-1]["id"], "depth", dep, "core", len(core), "neutral", len(neutral), "mobile", len(helpers - core), "%.0fs" % (time.time() - t0))
json.dump(picks, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "circuits.json"), "w"), indent=1)
