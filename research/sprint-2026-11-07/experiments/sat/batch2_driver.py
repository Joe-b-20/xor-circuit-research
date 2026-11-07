"""Parallel scoped-SAT campaign 2 (launched by batch2.sh; nothing here starts a solver unless
--shard is given).

  --prepare            pick the circuits (deterministic, seed 2026) -> batch2_circuits.json
  --plan               list the instance set with counts and an expected wall time for N shards
  --shard i --nshards N   worker i of N: runs items with index % N == i, in priority order

Instance set, priority order (limits in seconds):
  stage 1  10 random hunt-D 88 states (hunt/samplesD/samples.jsonl, distinct modulo byte rotation):
           every one-seed window (family A) with 2 <= k <= 8 at 60 s; every byte/half-byte block
           (family C) with free = k - targets_in_W <= 1 and 4 <= k <= 10 at 120 s          (Q5)
  stage 2  20 further structurally different 88 circuits (10 from hunt samples A/B/C, 10 from the
           kste corpus; cores from pes_lib.fan; a circuit is taken only if its rotation-normalised
           core shares <= 60% of its values with every core already taken, incl. circuits.json):
           one-seed windows k = 9..10 at 900 s; blocks (family C, k >= 4) at 1800 s if free <= 3,
           else 900 s
  stage 3  two-seed windows (family B) with 4 <= k <= 9 on repo, sampleC:1011, sampleA:1773 at 900 s
Sharding: deterministic global order (stage, k, free, circuit, scope); item j goes to shard j % N, so
all shards work on stage 1 first.  Each shard appends results_batch2.shard<i>.jsonl (schema of
results.jsonl + stage/shard); batch_summary.py merges them.  Idempotent: an instance is skipped if any
of results.jsonl, results_batch.jsonl, results_batch2*.jsonl holds it with UNSAT/SAT or a TIMEOUT at a
limit >= this one.  STOP: sat/STOP checked before every instance.  SAT: as batch_driver (found/,
write_circ.py verification, append sat/FOUND_87).
"""
import sys, os, json, time, hashlib, subprocess, random, glob, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.expanduser("~/xs-campaigns/2026-11-05-exit/pes"))
import sat87, run_scopes

HERE = os.path.dirname(os.path.abspath(__file__))
CIRC2 = os.path.join(HERE, "batch2_circuits.json")
LOG = os.path.join(HERE, "batch2.log")
STOP = os.path.join(HERE, "STOP")
FOUND = os.path.join(HERE, "FOUND_87")
NICE = 5
EXPECT = {2: 1, 3: 1, 4: 2, 5: 3, 6: 5, 7: 10, 8: 25}     # measured medians (s) for solved k
OVERHEAD = 6


def key(cid, W):
    return cid + ":" + hashlib.sha256(json.dumps(sorted(W)).encode()).hexdigest()[:16]


def log(msg, shard=None):
    line = time.strftime("%Y-%m-%d %H:%M:%S ") + ("[s%d] " % shard if shard is not None else "") + msg
    print(line); sys.stdout.flush()
    with open(LOG, "a") as f:
        f.write(line + "\n")


def rotsig(values):
    return min(tuple(sorted(sat87.rot(v, s) for v in values)) for s in range(4))


def core_of(sp, values):
    import pes_lib
    helpers = frozenset(v for v in values if v not in sat87.TSET)
    g, dep, neutral, downs, binds = pes_lib.fan(sp, helpers)
    touched = set()
    for R, A, hk, dd in neutral:
        touched |= set(R)
    core = helpers - touched
    return frozenset(min(sat87.rot(v, s) for s in range(4)) for v in core), dep, downs


def prepare():
    import pes_lib
    sp = pes_lib.make_space("mc", None)
    rng = random.Random(2026)
    out = {"stage1": [], "stage2": []}
    # stage 1: 10 random D states, distinct mod rotation
    lines = open(os.path.join(sat87.SPRINT, "hunt/samplesD/samples.jsonl")).read().splitlines()
    idx = [i for i, l in enumerate(lines) if json.loads(l).get("gates") == 88]
    rng.shuffle(idx)
    sigs = set()
    for i in idx:
        d = json.loads(lines[i])
        s = rotsig(d["values"])
        if s in sigs or sat87.wiring_from_values(d["values"]) is None:
            continue
        sigs.add(s)
        out["stage1"].append({"id": "sampleD:%d" % i, "arm": d.get("arm"), "worker": d.get("worker")})
        if len(out["stage1"]) == 10:
            break
    # stage 2: cores already used
    cores = []
    for c in json.load(open(os.path.join(HERE, "circuits.json"))):
        cores.append(frozenset(min(sat87.rot(v, s) for s in range(4)) for v in c["core"]))

    def distinct(core):
        return all(len(core & c) <= 0.6 * max(len(core), 1) for c in cores)

    cands = []
    for which, sub in (("sampleA", "samples.jsonl"), ("sampleC", "samplesC/samples.jsonl")):
        ls = open(os.path.join(sat87.SPRINT, "hunt", sub)).read().splitlines()
        for i, l in enumerate(ls):
            d = json.loads(l)
            if d.get("gates") == 88:
                cands.append(("%s:%d" % (which, i), d["values"]))
    rng.shuffle(cands)
    taken = 0
    for cid, vals in cands:
        if taken >= 10:
            break
        core, dep, downs = core_of(sp, vals)
        if downs:
            log("!!! down move at %s: %s" % (cid, downs))
        if not distinct(core):
            continue
        cores.append(core); taken += 1
        out["stage2"].append({"id": cid, "source": "hunt", "depth": dep, "core_size": len(core)})
    ks = json.load(open(os.path.join(sat87.SPRINT, "kste/data/kste_valuesets.json")))
    order_k = list(range(len(ks))); rng.shuffle(order_k)
    taken = 0
    for i in order_k:
        if taken >= 10:
            break
        vals = ks[i]
        if sat87.wiring_from_values(vals) is None:
            continue
        core, dep, downs = core_of(sp, vals)
        if downs:
            log("!!! down move at kste:%d: %s" % (i, downs))
        if not distinct(core):
            continue
        cores.append(core); taken += 1
        out["stage2"].append({"id": "kste:%d" % i, "source": "kste", "depth": dep, "core_size": len(core)})
    json.dump(out, open(CIRC2, "w"), indent=1)
    log("prepared: stage1 %d circuits, stage2 %d circuits" % (len(out["stage1"]), len(out["stage2"])))


def plan():
    c2 = json.load(open(CIRC2))
    items = []
    orders = {}

    def get(cid):
        if cid not in orders:
            run_scopes.CID[:] = [cid]
            orders[cid] = run_scopes.load(cid)
        return orders[cid]

    def tw(W):
        return sum(1 for t in sat87.TARGETS if t in W)

    for c in c2["stage1"]:
        o = get(c["id"])
        for name, W in run_scopes.scopes(o, "A", None):
            if 2 <= len(W) <= 8:
                items.append((1, c["id"], name, W, 60))
        for name, W in run_scopes.scopes(o, "C", None):
            if 4 <= len(W) <= 10 and len(W) - tw(W) <= 1:
                items.append((1, c["id"], name, W, 120))
    for c in c2["stage2"]:
        o = get(c["id"])
        for name, W in run_scopes.scopes(o, "A", None):
            if 9 <= len(W) <= 10:
                items.append((2, c["id"], name, W, 900))
        for name, W in run_scopes.scopes(o, "C", None):
            if len(W) >= 4:
                items.append((2, c["id"], name, W, 1800 if len(W) - tw(W) <= 3 else 900))
    for cid in ("repo", "sampleC:1011", "sampleA:1773"):
        o = get(cid)
        for name, W in run_scopes.scopes(o, "B", None):
            if 4 <= len(W) <= 9:
                items.append((3, cid, name, W, 900))
    # dedupe (circuit, W) keeping the first (highest priority) occurrence
    seen, uniq = set(), []
    for it in items:
        kk = key(it[1], it[3])
        if kk not in seen:
            seen.add(kk); uniq.append(it)
    uniq.sort(key=lambda x: (x[0], len(x[3]), len(x[3]) - tw(x[3]), x[1], x[2]))
    return orders, uniq


def prior():
    """key -> best prior record (result, limit) over all result files."""
    best = {}
    files = [os.path.join(HERE, f) for f in ("results.jsonl", "results_batch.jsonl", "results_batch2.jsonl")]
    files += glob.glob(os.path.join(HERE, "results_batch2.shard*.jsonl"))
    for path in files:
        if not os.path.exists(path):
            continue
        for line in open(path):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            k = key(r["circuit"], r["W"])
            cur = best.get(k)
            if cur is None or r["result"] in ("UNSAT", "SAT") or (r["result"] == "TIMEOUT" and r["limit"] > cur[1]):
                best[k] = (r["result"], r.get("limit", 0))
    return best


def skip(best, kk, limit):
    b = best.get(kk)
    return b is not None and (b[0] in ("UNSAT", "SAT") or (b[0] == "TIMEOUT" and b[1] >= limit))


def expected_secs(k, limit):
    return OVERHEAD + (EXPECT[k] if k in EXPECT else min(limit, 600 if k == 9 else limit))


def main():
    if "--prepare" in sys.argv:
        prepare(); return
    if not os.path.exists(CIRC2):
        prepare()
    orders, items = plan()
    best = prior()
    if "--plan" in sys.argv:
        N = int(sys.argv[sys.argv.index("--nshards") + 1]) if "--nshards" in sys.argv else 12
        for st in (1, 2, 3):
            its = [it for it in items if it[0] == st]
            todo = [it for it in its if not skip(best, key(it[1], it[3]), it[4])]
            ks = collections.Counter(len(it[3]) for it in todo)
            worst = sum(it[4] for it in todo) / 3600
            exp = sum(expected_secs(len(it[3]), it[4]) for it in todo) / 3600
            print("stage %d: %d instances (%d to do), k histogram %s, worst %.1f h serial, expected %.1f h serial = %.1f h at N=%d"
                  % (st, len(its), len(todo), sorted(ks.items()), worst, exp, exp / N, N))
        todo = [it for it in items if not skip(best, key(it[1], it[3]), it[4])]
        print("total %d instances (%d to do); expected %.1f h at N=%d, worst %.1f h at N=%d"
              % (len(items), len(todo), sum(expected_secs(len(it[3]), it[4]) for it in todo) / 3600 / N,
                 N, sum(it[4] for it in todo) / 3600 / N, N))
        return
    i = int(sys.argv[sys.argv.index("--shard") + 1]); N = int(sys.argv[sys.argv.index("--nshards") + 1])
    RES = os.path.join(HERE, "results_batch2.shard%d.jsonl" % i)
    mine = [it for j, it in enumerate(items) if j % N == i]
    log("shard start: %d items, %d already done" % (len(mine), sum(1 for it in mine if skip(best, key(it[1], it[3]), it[4]))), i)
    for st, cid, name, W, lim in mine:
        if os.path.exists(STOP):
            log("STOP present: stopping", i); return
        kk = key(cid, W)
        if skip(best, kk, lim):
            continue
        # batch.sh (serial) may have proved this one meanwhile: re-read its results (small file)
        rb = os.path.join(HERE, "results_batch.jsonl")
        if os.path.exists(rb):
            for line in open(rb):
                try:
                    r0 = json.loads(line)
                except ValueError:
                    continue
                if key(r0["circuit"], r0["W"]) == kk and r0["result"] in ("UNSAT", "SAT"):
                    best[kk] = (r0["result"], r0.get("limit", 0))
            if skip(best, kk, lim):
                continue
        order = orders[cid]
        vals = sat87.values_of(order)
        K = [v for v in vals if v not in W]
        assert sat87.split_closed(K)
        k = len(W); t = sum(1 for x in sat87.TARGETS if x in W)
        r = sat87.solve_instance(K, k - 1, lim, tag=name, tmpname="tmp_b2_shard%d.json" % i, nice=NICE)
        row = {"circuit": cid, "depth": sat87.check_circuit(order)[1], "scope": name, "k": k, "targets_in_W": t,
               "W": sorted(W), "result": r.get("result"), "secs": r.get("secs"), "solve_secs": r.get("solve_secs"),
               "nvars": r.get("nvars"), "nclauses": r.get("nclauses"), "limit": lim, "distinct": True,
               "stage": st, "shard": i, "time": time.strftime("%Y-%m-%dT%H:%M:%S")}
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
            log("!!!!! SAT %s %s k=%d -> circuit %s; verification:\n%s" % (cid, name, k, chk, ver.stdout), i)
        with open(RES, "a") as f:
            f.write(json.dumps(row) + "\n")
        best[kk] = (row["result"], lim)
        log("stage%d %-14s %-30s k=%2d tW=%2d free=%d %-8s %7.1fs" % (st, cid, name, k, t, k - t, row["result"], r.get("secs") or 0), i)
    log("shard complete", i)


if __name__ == "__main__":
    main()
