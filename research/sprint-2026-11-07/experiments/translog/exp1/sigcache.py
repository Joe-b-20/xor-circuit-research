#!/usr/bin/env python3
"""Incremental v3 plateau-signature cache for exp1 (runs during the campaign at low priority):
every 88 row with an identity in exp1/runs/E1/workers/*/translog.jsonl and every 88 sampler
record gets its signature (hunt/sig.py logic via translog/plateau_sig.py, ~33 ms each).
Writes exp1/sigcache.json {id or sampler hash: [sig, depth, n_neutral, n_downs]} every pass;
loops until exp1/DONE exists, then does a final pass.  Usage: sigcache.py [once]"""
import glob, json, os, sys, time
sys.path.insert(0, os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/translog"))
import plateau_sig as ps  # noqa: E402

E = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/translog/exp1")
OUT = os.path.join(E, "sigcache.json")
cache = json.load(open(OUT)) if os.path.exists(OUT) else {}
once = len(sys.argv) > 1 and sys.argv[1] == "once"


def passes():
    n = 0
    t0 = time.time()
    for tl in sorted(glob.glob(os.path.join(E, "runs/E1/workers/*/translog.jsonl"))):
        try:
            with open(tl) as f:
                for line in f:
                    try:
                        r = json.loads(line)
                    except ValueError:
                        break           # partial last line
                    i = r.get("id")
                    if i and i not in cache and r.get("v"):
                        sig, info = ps.sig_of(r["v"])
                        cache[i] = [sig, info[0], info[1], info[2]] if sig else [None, info, 0, 0]
                        n += 1
        except OSError:
            pass
    s = os.path.join(E, "samples/samples.jsonl")
    if os.path.exists(s):
        for line in open(s):
            try:
                r = json.loads(line)
            except ValueError:
                break
            if r["gates"] == 88 and r["hash"] not in cache:
                sig, info = ps.sig_of(r["values"])
                cache[r["hash"]] = [sig, info[0], info[1], info[2]] if sig else [None, info, 0, 0]
                n += 1
    tmp = OUT + ".tmp"
    json.dump(cache, open(tmp, "w"))
    os.replace(tmp, OUT)
    print(time.strftime("%H:%M:%SZ", time.gmtime()), f"+{n} signatures ({time.time() - t0:.0f} s), total {len(cache)}", flush=True)


while True:
    done = os.path.exists(os.path.join(E, "DONE"))
    passes()
    if once or done:
        break
    time.sleep(60)
if not once:
    passes()
print("final", len(cache))
