"""c4_p2_classify.py: for each c3 candidate (one source file each), what did its run end at, and was the
90-gate state the run's final best (a trap) or a transient on the way to 89? Read-only, no pes_lib."""
import json, os
from collections import Counter
HOME = os.path.expanduser("~")
OUT = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(f"{OUT}/c3_result.json"))
rows = R["candidates"]
assert len({r["example"] for r in rows}) == len(rows), "example files are not unique; join is ambiguous"
summary = Counter()
print("file | run end best | last 90 'best' event is final best? | in_B1 | R1 down into L0 | BFS hit")
for r in rows:
    f = r["example"].replace("~", HOME)
    bests = []; end_best = None; final_g = None
    for line in open(f):
        try:
            e = json.loads(line)
        except Exception:
            continue
        if e.get("ev") == "best" or ("values" in e and e.get("g") is not None):
            bests.append((e.get("g"), e.get("d")))
            final_g = (e.get("g"), e.get("d"))
        if e.get("ev") == "end":
            end_best = e.get("best")
    if end_best is None and bests:
        end_best = min(g for g, d in bests if g is not None)
    trap = (end_best == 90)
    r["run_end_best"] = end_best; r["final_best_event"] = final_g; r["trap"] = trap
    key = ("TRAP(run ended 90)" if trap else f"transient(run ended {end_best})",
           "L0-reached" if r["bfs_hit"] == "L0" else ("stuck" if r["bfs_exhausted"] else "cut"))
    summary[key] += 1
    print(f"{os.path.basename(f):40s} | {end_best} | {final_g} | B1={r['in_B1']} | down->L0={r['downs_into_L0']} | {r['bfs_hit'] or ('stuck' if r['bfs_exhausted'] else 'cut@3000')}")
print("\nsummary:", dict(summary))
json.dump(R, open(f"{OUT}/c4_result.json", "w"), indent=1)
