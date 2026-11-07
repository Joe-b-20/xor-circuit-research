#!/usr/bin/env python3
"""Plan (and with --apply, do) the circuits/ update from sprint run directories.

Usage: harvest_sprint.py [--apply] RUN_DIR [RUN_DIR ...]
A pool point is kept when no circuit already in circuits/<map>/ has as few gates at no more
depth and no NIST circuit does either.  Our circuits a kept point dominates are listed for
removal.  The earliest-found non-seed record is used.  Adapted from
~/xs-campaigns/2026-10-31-long/harvest.py (same rules).
"""
import glob, json, os, re, subprocess, sys

REPO = os.path.expanduser("~/xor-circuit-research")
NIST_EXTRA = {"aes-invmixcolumns": [(119, 5), (106, 6), (102, 7), (90, 20)],
              "aes-mixcolumns": [(97, 3), (90, 4), (88, 5), (92, 6)]}


def dominated(p, others):
    return any(g <= p[0] and d <= p[1] for g, d in others)


def ours(m):
    pts = {}
    for f in glob.glob(f"{REPO}/circuits/{m}/{m}-xor*-depth*.circ.txt"):
        g, d = map(int, re.search(r"-xor(\d+)-depth(\d+)\.circ\.txt$", f).groups())
        pts[(g, d)] = f
    return pts


def nist(m):
    pts = list(NIST_EXTRA.get(m, []))
    for f in glob.glob(f"{REPO}/search/seeds/{m}/nist-g*-d*.json"):
        pts.append(tuple(map(int, re.search(r"nist-g(\d+)-d(\d+)\.json$", f).groups())))
    return pts


_kinds = {}


def kind(run, path):
    index = os.path.join(run, path.split("/records/")[0], "records.jsonl")
    if index not in _kinds:
        _kinds[index] = {}
        if os.path.exists(index):
            _kinds[index] = {r["path"]: r.get("kind") for r in map(json.loads, open(index)) if r.get("path")}
    return _kinds[index].get(path)


def plan(runs):
    adds, removes = [], []
    for run in runs:
        run = run.rstrip("/") + "/"
        for pf in sorted(glob.glob(run + "pool/*.json")):
            m = os.path.basename(pf)[:-5]
            pool = json.load(open(pf))["points"]
            pts = {(p["gates"], p["depth"]): p["entries"] for p in pool}
            front = [p for p in pts if not any(q != p and q[0] <= p[0] and q[1] <= p[1] for q in pts)]
            have = ours(m)
            for p in sorted(front, key=lambda x: x[1]):
                if dominated(p, have) or dominated(p, nist(m)):
                    continue
                recs = sorted((e for e in pts[p] if kind(run, e["path"]) != "seed"), key=lambda e: e["t"])
                if not recs:
                    continue
                adds.append((m, p, run + recs[0]["path"]))
                for q, f in have.items():
                    if p[0] <= q[0] and p[1] <= q[1]:
                        removes.append((m, q, f))
    # a later run may dominate an earlier add; keep only nondominated adds per map
    keep = []
    for a in adds:
        if not any(b != a and b[0] == a[0] and b[1][0] <= a[1][0] and b[1][1] <= a[1][1] for b in adds):
            keep.append(a)
    return keep, sorted(set(removes))


def main():
    args = [a for a in sys.argv[1:] if a != "--apply"]
    adds, removes = plan(args)
    for m, p, path in adds:
        print(f"ADD    {m} {p[0]}@{p[1]}  {path}")
    for m, q, f in removes:
        print(f"REMOVE {m} {q[0]}@{q[1]}  {f}")
    if "--apply" not in sys.argv:
        return
    for m, q, f in removes:
        logs = f"{REPO}/circuits/{m}/logs/{m}-xor{q[0]}-depth{q[1]}"
        subprocess.run(["git", "rm", "-rq", f] + ([logs] if os.path.isdir(logs) else []), cwd=REPO, check=True)
    for m, p, path in adds:
        subprocess.run([sys.executable, "circuits/add.py", path, "--version", "v8"], cwd=REPO, check=True)


main()
