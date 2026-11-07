"""Overnight scoped-SAT batch (run via batch.sh; `python3 batch_driver.py --plan` only lists it).

Stages, in order of promise:
  1  output windows with 1..3 free values (k - targets_in_W in 1..3, k >= 4): families C and A,
     repo + six picked circuits, 1800 s each
  2  all one-seed windows (family A) with k = 9..10, repo + six picked circuits, 900 s each
  3  two-seed windows (family B) with k = 4..10 on the repo circuit, 900 s each, k ascending
Idempotent: an instance (circuit, W) already in results_batch.jsonl, or already UNSAT in
results.jsonl (the 60 s campaign), is skipped.  Stops cleanly when sat/STOP exists (checked before
every instance).  One solver child at a time, nice 10 (sat87.solve_instance).
On SAT: full circuit decoded and re-checked (sat87.check_circuit), dumped to found/, written as
.circ.txt and verified by write_circ.py (repo check.py + unit vectors), and sat/FOUND_87 touched.
"""
import sys, os, json, time, hashlib, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sat87, run_scopes

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results_batch.jsonl")
OLD = os.path.join(HERE, "results.jsonl")
LOG = os.path.join(HERE, "batch.log")
STOP = os.path.join(HERE, "STOP")
FOUND = os.path.join(HERE, "FOUND_87")
CIRCUITS = ["repo"] + [c["id"] for c in json.load(open(os.path.join(HERE, "circuits.json")))]


def key(cid, W):
    return cid + ":" + hashlib.sha256(json.dumps(sorted(W)).encode()).hexdigest()[:16]


def done_keys():
    done = set()
    for path, only_unsat in ((RES, False), (OLD, True)):
        if not os.path.exists(path):
            continue
        for line in open(path):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if only_unsat and r.get("result") != "UNSAT":
                continue
            done.add(key(r["circuit"], r["W"]))
    return done


def plan():
    """List of (stage, cid, scope_name, W, limit)."""
    orders = {}
    for cid in CIRCUITS:
        run_scopes.CID[:] = [cid]
        orders[cid] = run_scopes.load(cid)
    items = []
    # stage 1
    for cid in CIRCUITS:
        o = orders[cid]
        sc = run_scopes.scopes(o, "C", None) + run_scopes.scopes(o, "A", None)
        seen = set()
        for name, W in sc:
            k = len(W); tw = sum(1 for t in sat87.TARGETS if t in W)
            if k >= 4 and 1 <= k - tw <= 3 and W not in seen:
                seen.add(W); items.append((1, cid, name, W, 1800))
    items[:] = sorted(items, key=lambda x: (x[0], len(x[3]) - sum(1 for t in sat87.TARGETS if t in x[3]), len(x[3])))
    # stage 2
    s2 = []
    for cid in CIRCUITS:
        for name, W in run_scopes.scopes(orders[cid], "A", None):
            if 9 <= len(W) <= 10:
                s2.append((2, cid, name, W, 900))
    s2.sort(key=lambda x: len(x[3]))
    # stage 3
    s3 = []
    for name, W in run_scopes.scopes(orders["repo"], "B", None):
        if 4 <= len(W) <= 10:
            s3.append((3, "repo", name, W, 900))
    s3.sort(key=lambda x: len(x[3]))
    return orders, items + s2 + s3


def log(msg):
    line = time.strftime("%Y-%m-%d %H:%M:%S ") + msg
    print(line); sys.stdout.flush()
    with open(LOG, "a") as f:
        f.write(line + "\n")


def main():
    orders, items = plan()
    if "--plan" in sys.argv:
        import collections
        c = collections.Counter(); t = collections.Counter()
        for st, cid, name, W, lim in items:
            c[st] += 1; t[st] += lim
        done = done_keys()
        for st in sorted(c):
            ks = collections.Counter(len(W) for s_, cid, name, W, lim in items if s_ == st and key(cid, W) not in done)
            print("stage %d: %d instances, limit sum %.1f h; k histogram of those not yet done: %s"
                  % (st, c[st], t[st] / 3600, sorted(ks.items())))
        print("total %d instances, worst case %.1f h" % (len(items), sum(t.values()) / 3600))
        done = done_keys()
        print("already done (skipped):", sum(1 for st, cid, name, W, lim in items if key(cid, W) in done))
        return
    done = done_keys()
    log("batch start: %d planned instances, %d already done" % (len(items), sum(1 for it in items if key(it[1], it[3]) in done)))
    for st, cid, name, W, lim in items:
        if os.path.exists(STOP):
            log("STOP file present: stopping cleanly"); return
        if key(cid, W) in done:
            continue
        order = orders[cid]
        vals = sat87.values_of(order)
        K = [v for v in vals if v not in W]
        assert sat87.split_closed(K)
        k = len(W); tw = sum(1 for t in sat87.TARGETS if t in W)
        r = sat87.solve_instance(K, k - 1, lim, tag=name, tmpname="tmp_batch_req.json")
        row = {"circuit": cid, "depth": sat87.check_circuit(order)[1], "scope": name, "k": k, "targets_in_W": tw,
               "W": sorted(W), "result": r.get("result"), "secs": r.get("secs"), "solve_secs": r.get("solve_secs"),
               "nvars": r.get("nvars"), "nclauses": r.get("nclauses"), "limit": lim, "distinct": True,
               "stage": st, "time": time.strftime("%Y-%m-%dT%H:%M:%S")}
        if r.get("result") == "ERROR":
            row["err"] = r.get("err")
        if r.get("result") == "SAT":
            new = [tuple(x) for x in r["new_gates"]]
            full = [(v, a, b) for v, a, b in order if v in set(K)] + new
            chk = sat87.check_circuit(full)
            row["found"] = chk; row["full"] = full
            h = hashlib.sha256(json.dumps(full).encode()).hexdigest()[:12]
            fpath = os.path.join(HERE, "found", "found_%s.json" % h)
            json.dump({"circuit": cid, "scope": name, "order": full}, open(fpath, "w"))
            ver = subprocess.run(["python3", os.path.join(HERE, "write_circ.py"), fpath], capture_output=True, text=True)
            row["verify"] = ver.stdout + ver.stderr
            with open(FOUND, "a") as f:
                f.write("%s %s %s check=%s\n%s\n" % (time.strftime("%Y-%m-%dT%H:%M:%S"), cid, name, chk, ver.stdout))
            log("!!!!! SAT %s %s k=%d -> circuit %s; verification:\n%s" % (cid, name, k, chk, ver.stdout))
        with open(RES, "a") as f:
            f.write(json.dumps(row) + "\n")
        done.add(key(cid, W))
        log("stage%d %-14s %-30s k=%2d tW=%2d free=%d %-8s %7.1fs" % (st, cid, name, k, tw, k - tw, row["result"], r.get("secs") or 0))
    log("batch complete")


if __name__ == "__main__":
    main()
