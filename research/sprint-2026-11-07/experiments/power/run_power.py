#!/usr/bin/env python3
"""Part 2: run the sprint's instrument I(K, k-1) on the power-control windows (windows.json), ONE
solver child at a time under nice 8, within a global wall budget.  Reuses sat/sat87.py's encoder and
sat/solve_child.py unchanged (the request file lives here, not in sat/).  Sprint limits per family:
A k <= 8: 60 s (batch2 stage 1); A k = 9..10: 900 s; C: 1800 s if free <= 3 else 900 s (batch_driver
stage 1 / batch2 stage 2); B: 900 s.  Priority: windows whose K is contained in the known improvement
(expected SAT: positive control of the solver), then windows contained in any known smaller circuit,
then family A k <= 8 round-robin over anchors by k, then C, then A k = 9..10, then B (<= NB per anchor,
smallest k first).  An instance whose sprint limit exceeds the remaining budget runs with the remaining
budget and is flagged budget_truncated.  Appends results.jsonl (idempotent on (anchor, W)), run.log.
Usage: nice -n 8 python3 run_power.py BUDGET_MINUTES [NB_per_anchor]
"""
import sys, os, json, time, hashlib, subprocess, collections
H = os.path.expanduser("~")
S = H + "/xs-campaigns/2026-11-07-sprint"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, S + "/sat")
import sat87  # noqa: E402

RES = os.path.join(HERE, "results.jsonl")
LOG = os.path.join(HERE, "run.log")
CHILD = os.path.join(S, "sat", "solve_child.py")
NICE = 8


def log(msg):
    line = time.strftime("%Y-%m-%d %H:%M:%S ") + msg
    print(line); sys.stdout.flush()
    with open(LOG, "a") as f:
        f.write(line + "\n")


def key(aid, W):
    return aid + ":" + hashlib.sha256(json.dumps(sorted(W)).encode()).hexdigest()[:16]


def sprint_limit(r):
    if r["fam"] == "A":
        return 60 if r["k"] <= 8 else 900
    if r["fam"] == "C":
        return 1800 if r["free"] <= 3 else 900
    return 900


def solve(K, m, limit):
    req = {"K": sorted(K), "m": m, "solver": "cadical195", "distinct": True, "symbreak": True}
    tmp = os.path.join(HERE, "tmp_power_req.json")
    json.dump(req, open(tmp, "w"))
    t0 = time.time()
    try:
        p = subprocess.run(["nice", "-n", str(NICE), "python3", CHILD, tmp], capture_output=True, text=True, timeout=limit + 5)
        out = p.stdout.strip().splitlines()
        res = json.loads(out[-1]) if out else {"result": "ERROR", "err": p.stderr[-500:]}
    except subprocess.TimeoutExpired:
        res = {"result": "TIMEOUT"}
    res["secs"] = round(time.time() - t0, 1)
    return res


def main():
    budget = float(sys.argv[1]) * 60
    NB = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    anchors = {a["id"]: a for a in json.load(open(os.path.join(HERE, "anchors.json")))}
    rows = json.load(open(os.path.join(HERE, "windows.json")))
    # k = 1 (m = 0) is not an instance the sprint ran (batch2 stage 1 starts at k = 2) and is trivially
    # UNSAT (the removed value is an output with no replacement); the first run recorded them as ERROR.
    rows = [r for r in rows if r["k"] >= 2]
    for r in rows:
        r["limit"] = sprint_limit(r)
    # priority classes
    P0 = sorted([r for r in rows if r["contained_truth"]], key=lambda r: r["k"])
    if "nop0" in sys.argv:
        P0 = []
    P1 = sorted([r for r in rows if not r["contained_truth"] and r["n_contained_corpus"]], key=lambda r: r["k"])
    rest = [r for r in rows if not r["contained_truth"] and not r["n_contained_corpus"]]

    def rr(items, keyf):
        """round robin over anchors, each anchor's list sorted by keyf."""
        per = collections.defaultdict(list)
        for r in items:
            per[r["anchor"]].append(r)
        for a in per:
            per[a].sort(key=keyf)
        out = []
        while any(per.values()):
            for a in list(per):
                if per[a]:
                    out.append(per[a].pop(0))
        return out
    P2 = rr([r for r in rest if r["fam"] == "A" and r["k"] <= 8], lambda r: (r["k"], r["free"]))
    P3 = rr([r for r in rest if r["fam"] == "C"], lambda r: (r["free"], r["k"]))
    P4 = rr([r for r in rest if r["fam"] == "A" and r["k"] >= 9], lambda r: (r["k"], r["free"]))
    Bs = collections.defaultdict(list)
    for r in rest:
        if r["fam"] == "B":
            Bs[r["anchor"]].append(r)
    Bsel = []
    for a in Bs:
        Bs[a].sort(key=lambda r: (r["k"], r["free"]))
        Bsel += Bs[a][:NB]
    P5 = rr(Bsel, lambda r: (r["k"], r["free"]))
    plan = [(0, r) for r in P0] + [(1, r) for r in P1] + [(2, r) for r in P2] + [(3, r) for r in P3] + [(4, r) for r in P4] + [(5, r) for r in P5]
    done = set()
    if os.path.exists(RES):
        for line in open(RES):
            try:
                d = json.loads(line)
            except ValueError:
                continue
            done.add(key(d["anchor"], d["W"]))
    log("plan: P0 %d P1 %d P2 %d P3 %d P4 %d P5 %d (of %d windows); budget %.0f min; already done %d"
        % (len(P0), len(P1), len(P2), len(P3), len(P4), len(P5), len(rows), budget / 60, len(done)))
    t_start = time.time()
    orders = {}
    n = 0
    for pri, r in plan:
        kk = key(r["anchor"], r["W"])
        if kk in done:
            continue
        remaining = budget - (time.time() - t_start)
        if remaining < 20:
            log("budget exhausted: stopping before priority %d %s %s" % (pri, r["anchor"], r["scope"]))
            break
        a = anchors[r["anchor"]]
        if r["anchor"] not in orders:
            orders[r["anchor"]] = sat87.wiring_from_values(a["values"])
        order = orders[r["anchor"]]
        vals = sat87.values_of(order)
        Wset = set(r["W"])
        K = [v for v in vals if v not in Wset]
        assert sat87.split_closed(K)
        k = len(Wset)
        lim = min(r["limit"], remaining)
        res = solve(K, k - 1, lim)
        row = {"anchor": r["anchor"], "kind": a["kind"], "gates": a["gates"], "scope": r["scope"], "fam": r["fam"], "k": k,
               "tW": r["tW"], "free": r["free"], "W": sorted(Wset), "contained_truth": r["contained_truth"],
               "n_contained_corpus": r["n_contained_corpus"], "priority": pri, "result": res.get("result"),
               "secs": res.get("secs"), "solve_secs": res.get("solve_secs"), "nvars": res.get("nvars"), "nclauses": res.get("nclauses"),
               "limit": round(lim), "sprint_limit": r["limit"], "budget_truncated": lim < r["limit"],
               "time": time.strftime("%Y-%m-%dT%H:%M:%S")}
        if res.get("result") == "ERROR":
            row["err"] = res.get("err")
        if res.get("result") == "SAT":
            new = [tuple(x) for x in res["new_gates"]]
            full = [(v, a_, b_) for v, a_, b_ in order if v in set(K)] + new
            chk = sat87.check_circuit(full)
            fv = set(sat87.values_of(full))
            row["found"] = chk
            row["found_values"] = sorted(fv)
            row["found_equals_truth"] = fv == set(a["truth"]["values"])
            row["found_n_new_outside_truth"] = len(fv - set(a["truth"]["values"]))
        with open(RES, "a") as f:
            f.write(json.dumps(row) + "\n")
        done.add(kk)
        n += 1
        log("P%d %-26s %-28s k=%2d tW=%2d free=%2d cont=%d/%d %-8s %7.1fs%s%s"
            % (pri, r["anchor"], r["scope"], k, r["tW"], r["free"], int(r["contained_truth"]), r["n_contained_corpus"],
               row["result"], res.get("secs") or 0, " TRUNC" if row["budget_truncated"] else "",
               (" FOUND %s eq_truth=%s" % (row.get("found"), row.get("found_equals_truth"))) if row["result"] == "SAT" else ""))
    log("run complete: %d instances in %.1f min" % (n, (time.time() - t_start) / 60))


if __name__ == "__main__":
    main()
