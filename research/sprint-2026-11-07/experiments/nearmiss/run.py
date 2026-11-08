"""Sequential driver: ONE solver child at a time (nice -n 8), per-instance wall limit, per-file budget.
usage: python3 run.py TOTAL_BUDGET_S file1.json:budget_s file2.json:budget_s ...
Appends one json line per instance to results.jsonl; prints a table row per instance to stdout.
A SAT is decoded, verified (sat87.check_circuit), written to found/ and FOUND_87, and announced."""
import json, os, sys, time, subprocess
from common import *
import sat87

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results.jsonl")
T0 = time.time()
total_budget = float(sys.argv[1])


def done_names():
    s = set()
    if os.path.exists(RES):
        for l in open(RES):
            d = json.loads(l)
            if d.get("result") in ("SAT", "UNSAT"):
                s.add((d["name"], d["limit"]))
    return s


def found(x, r):
    new = [tuple(g) for g in r["new_gates"]]
    base = sat87.wiring_from_values(x["K"])
    order = base + new
    gates, depth, nd = sat87.check_circuit(order)
    fn = os.path.join(HERE, "found", "found_%s.json" % x["name"].replace(":", "_").replace(",", "+"))
    json.dump({"order": order, "scope": x["name"], "circuit": x["family"], "K": x["K"], "new_gates": new,
               "gates": gates, "depth": depth, "distinct": nd}, open(fn, "w"))
    p = subprocess.run(["python3", os.path.join(SAT, "write_circ.py"), fn], capture_output=True, text=True)
    msg = "\n!!!!! SAT: %s -> %d gates (%d distinct), depth %d. %s\n%s\n" % (x["name"], gates, nd, depth, fn, p.stdout + p.stderr)
    print(msg, flush=True)
    open(os.path.join(HERE, "FOUND_87"), "a").write(time.strftime("%Y-%m-%dT%H:%M:%SZ ", time.gmtime()) + msg)


skip = done_names()
print("%-34s %-6s %3s %3s %3s %-8s %7s %7s %8s" % ("name", "family", "k", "m", "tN", "result", "wall", "solve", "clauses"), flush=True)
for arg in sys.argv[2:]:
    fn, bud = arg.split(":")
    bud = float(bud)
    tf = time.time()
    for x in json.load(open(fn)):
        if (x["name"], x["limit"]) in skip:
            continue
        if time.time() - tf > bud or time.time() - T0 > total_budget:
            print("budget exhausted before", x["name"], flush=True)
            break
        lim = min(x["limit"], max(10.0, total_budget - (time.time() - T0)))
        r = sat87.solve_instance(x["K"], x["m"], lim, tag=x["name"], tmpname="tmp_nearmiss.json", nice=8)
        row = {"name": x["name"], "family": x["family"], "k": x["k"], "m": x["m"], "targets_needed": x["targets_needed"],
               "W": x["W"], "nK": len(x["K"]), "result": r.get("result"), "secs": r.get("secs"), "solve_secs": r.get("solve_secs"),
               "nvars": r.get("nvars"), "nclauses": r.get("nclauses"), "limit": lim, "note": x["note"],
               "time": time.strftime("%H:%M:%S", time.gmtime())}
        if r.get("result") == "ERROR":
            row["err"] = r.get("err")
        open(RES, "a").write(json.dumps(row) + "\n")
        print("%-34s %-6s %3d %3d %3d %-8s %7.1f %7s %8s" % (x["name"], x["family"], x["k"], x["m"], len(x["targets_needed"]),
              r.get("result"), r.get("secs", 0), r.get("solve_secs"), r.get("nclauses")), flush=True)
        if r.get("result") == "SAT":
            found(x, r)
print("all done, total %.0f s" % (time.time() - T0), flush=True)
