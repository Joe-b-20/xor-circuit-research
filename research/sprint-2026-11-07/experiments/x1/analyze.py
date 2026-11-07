#!/usr/bin/env python3
"""X1 summary: per map, best gates at the cap for the fresh-root arm and the NIST-seeded arm,
NIST's gates at that depth, our repo best at <= cap, W = (NIST - fresh)/NIST and the seeded gain.
Also the time of each arm's last improvement.  Usage: analyze.py RUN_DIR [RUN_DIR ...]"""
import json, os, re, sys

REPO = "/home/joebachir20/xor-circuit-research"


def repo_best(mapname, cap):
    best = None
    d = os.path.join(REPO, "circuits", mapname)
    for f in os.listdir(d):
        m = re.match(r".*-xor(\d+)-depth(\d+)\.circ\.txt$", f)
        if m and int(m.group(2)) <= cap:
            g = int(m.group(1))
            if best is None or g < best:
                best = g
    return best


def nist_at(mapname, cap):
    best = None
    d = os.path.join(REPO, "search", "seeds", mapname)
    if not os.path.isdir(d):
        return None
    for f in os.listdir(d):
        m = re.match(r"nist-g(\d+)-d(\d+)\.json$", f)
        if m and int(m.group(2)) <= cap:
            g = int(m.group(1))
            if best is None or g < best:
                best = g
    return best


rows = {}
for run in sys.argv[1:]:
    plan = json.load(open(os.path.join(run, "plan.json")))
    for w in plan.get("workers", []):
        wid = w.get("id") or w.get("worker")
        target = w.get("target")
        cap = w.get("depth_cap")
        arm = "fresh" if "-fresh-" in wid else "nist"
        st_path = os.path.join(run, "workers", wid, "status.json")
        best = None
        last_t = None
        if os.path.exists(st_path):
            st = json.load(open(st_path))
            b = st.get("best") or {}
            best = (b.get("gates"), b.get("depth"))
        ev = os.path.join(run, "workers", wid, "events.jsonl")
        if os.path.exists(ev):
            for line in open(ev):
                if '"ev":"improve"' in line:
                    e = json.loads(line)
                    last_t = e["t"]
        rows.setdefault((target, cap), {})[arm] = (best, last_t)

print(f"{'map':28s} cap  NIST  repo  fresh      nist-seeded   W=(NIST-fresh)/NIST  seeded gain  last improve (fresh / nist) s")
for (target, cap), arms in sorted(rows.items()):
    n = nist_at(target, cap) or (88 if target == "aes-mixcolumns" else None)
    r = repo_best(target, cap)
    fb, ft = arms.get("fresh", ((None, None), None))
    nb, nt = arms.get("nist", ((None, None), None))
    W = (n - fb[0]) / n if (n and fb and fb[0]) else None
    G = (n - nb[0]) / n if (n and nb and nb[0]) else None
    print(f"{target:28s} {cap!s:4s} {n!s:5s} {r!s:5s} {str(fb):10s} {str(nb):13s} "
          f"{('%.3f' % W) if W is not None else '-':>19s}  {('%.3f' % G) if G is not None else '-':>11s}  "
          f"{ft if ft is None else int(ft)} / {nt if nt is None else int(nt)}")
