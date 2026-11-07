"""satmob/mob.py -- factor-structured scoped SAT for an 87 (implements sat/MOBILE_ENCODING.md).

Everything here is an instance of sat87's I(K, m) (sat/sat87.py, unchanged, imported): K = S \\ W is
a split-closed subset of an 88 circuit S, m = |W| - 1.  UNSAT means: no circuit with <= 87 gates has
a value set containing K.  The only difference to sat/ is HOW W is chosen: from the plateau's
factor structure (core / mobile helpers / consumer roots) instead of a seed value.

  python3 mob.py analyze CID            compute core, mobile, components; write comp_<cid>.json
  python3 mob.py run CID LEVELS LIMIT [pool]   run the instances (one solver child at a time, nice 8)
      LEVELS: comma list of 1 (single components), 2 (pairs), 3 (triples), all (whole mobile part)
      pool:   full (default, exact meaning above) | span (operands restricted to GF(2)-span of the
              component's leaves: a WEAKER statement, recorded with pool="span")
CID as in sat/run_scopes.load: repo | sampleA:<line> | sampleC:<line> | sampleD:<line> | kste:<i>.
Results: results.jsonl (sat87 schema + component description), run.log, found/, FOUND_87, STOP.
"""
import sys, os, json, time, hashlib, subprocess, itertools, collections
HERE = os.path.dirname(os.path.abspath(__file__))
SAT = os.path.join(os.path.dirname(HERE), "sat")
sys.path.insert(0, SAT)
sys.path.insert(0, os.path.expanduser("~/xs-campaigns/2026-11-05-exit/pes"))
import sat87, run_scopes  # noqa: E402

run_scopes.ANYPAIR = True          # minimal forced removal (any-pair closure), as dsizes.py scope (c)
RES = os.path.join(HERE, "results.jsonl")
LOG = os.path.join(HERE, "run.log")
FOUND = os.path.join(HERE, "FOUND_87")
STOP = os.path.join(HERE, "STOP")
NICE = 8


def log(msg):
    line = time.strftime("%Y-%m-%d %H:%M:%S ") + msg
    print(line); sys.stdout.flush()
    with open(LOG, "a") as f:
        f.write(line + "\n")


def load(cid):
    run_scopes.CID[:] = [cid]
    return run_scopes.load(cid)


# ------------------------------------------------------------------ plateau structure
def fan_core(order):
    """Core / mobile via pes_lib.fan (remove1-neutral moves).  Returns dict."""
    import pes_lib
    sp = pes_lib.make_space("mc", None)
    vals = sat87.values_of(order)
    helpers = frozenset(v for v in vals if v not in sat87.TSET)
    t0 = time.time()
    g, dep, neutral, downs, binds = pes_lib.fan(sp, helpers)
    touched, moves = set(), []
    for R, A, hk, dd in neutral:
        touched |= set(R)
        moves.append({"R": sorted(R), "A": sorted(A), "depth": dd})
    return {"gates": g, "depth": dep, "fan_secs": round(time.time() - t0, 1),
            "mobile": sorted(touched), "core": sorted(helpers - touched),
            "n_neutral": len(neutral), "downs": [list(map(str, x)) for x in downs], "moves": moves}


def n_splits(vals):
    """For each value of S: number of unordered pairs {a, b} in INPUTS u S with a ^ b = v (wiring
    ambiguity of the value set)."""
    pool = set(sat87.INPUTS) | set(vals)
    out = {}
    for v in vals:
        n = 0
        for a in pool:
            b = a ^ v
            if b in pool and a < b:
                n += 1
        out[v] = n
    return out


def components(order, mobile):
    """Connected components of the bipartite graph mobile -- consumers (under the wiring)."""
    users = sat87.dependents(order)
    M = set(mobile)
    adj = collections.defaultdict(set)
    for m in M:
        for u in users[m]:
            adj[m].add(u); adj[u].add(m)
    seen, comps = set(), []
    for m in sorted(M):
        if m in seen:
            continue
        stack, comp = [m], set()
        while stack:
            x = stack.pop()
            if x in comp:
                continue
            comp.add(x)
            stack.extend(adj[x] - comp)
        seen |= comp
        comps.append({"mobile": sorted(comp & M), "roots": sorted(comp - M)})
    return comps


def leaves(order, W):
    """Operands (under the wiring) of removed values that are themselves kept or inputs."""
    Wset = set(W)
    L = set()
    for v, a, b in order:
        if v in Wset:
            for o in (a, b):
                if o not in Wset:
                    L.add(o)
    return sorted(L)


def span_basis(vecs):
    basis = []
    for v in vecs:
        for b in basis:
            v = min(v, v ^ b)
        if v:
            basis.append(v)
    return basis


def in_span(basis, v):
    for b in basis:
        v = min(v, v ^ b)
    return v == 0


def describe(order, comps, idxs):
    """Window W for the union of components idxs; returns (name, W, desc)."""
    seeds = set()
    for i in idxs:
        seeds |= set(comps[i]["mobile"]) | set(comps[i]["roots"])
    W = frozenset(run_scopes.window(order, sorted(seeds)))
    name = "M:" + "+".join("c%d" % i for i in idxs)
    tW = sum(1 for t in sat87.TARGETS if t in W)
    desc = {"components": list(idxs), "n_mobile": sum(len(comps[i]["mobile"]) for i in idxs),
            "n_roots": sum(len(comps[i]["roots"]) for i in idxs), "seeds": len(seeds),
            "forced_extra": len(W) - len(seeds), "leaves": leaves(order, W)}
    return name, W, desc, tW


def analyze(cid, write=True):
    order = load(cid)
    g, d, nd = sat87.check_circuit(order)
    assert g == 88 and nd == 88
    vals = sat87.values_of(order)
    fc = fan_core(order)
    assert fc["gates"] == 88
    comps = components(order, fc["mobile"])
    ns = n_splits(vals)
    amb = [v for v in vals if ns[v] > 1]
    info = {"circuit": cid, "depth": d, "fan": fc, "components": comps,
            "ambiguous_values": {"%08x" % v: ns[v] for v in amb}}
    # window sizes
    rows = []
    for i in range(len(comps)):
        name, W, desc, tW = describe(order, comps, [i])
        rows.append({"idx": i, "mobile": ["%08x" % v for v in comps[i]["mobile"]],
                     "roots": ["%08x" % v for v in comps[i]["roots"]],
                     "root_targets": sum(1 for r in comps[i]["roots"] if r in sat87.TSET),
                     "k": len(W), "tW": tW, "free": len(W) - 1 - tW, "forced_extra": desc["forced_extra"],
                     "n_leaves": len(desc["leaves"]), "W": sorted(W)})
    info["component_windows"] = rows
    name, W, desc, tW = describe(order, comps, list(range(len(comps))))
    info["whole_mobile"] = {"k": len(W), "tW": tW, "free": len(W) - 1 - tW, "forced_extra": desc["forced_extra"],
                            "n_leaves": len(desc["leaves"])}
    if write:
        json.dump(info, open(os.path.join(HERE, "comp_%s.json" % cid.replace(":", "_")), "w"), indent=1)
    print("circuit %s depth %d: core %d, mobile %d, neutral moves %d, downs %s; %d components; ambiguous splits: %d values"
          % (cid, d, len(fc["core"]), len(fc["mobile"]), fc["n_neutral"], fc["downs"], len(comps), len(amb)))
    for r in rows:
        print("  c%-2d mobile %d roots %d (targets %d)  k=%2d tW=%2d free=%d forced_extra=%d leaves=%d  mobile=%s"
              % (r["idx"], len(r["mobile"]), len(r["roots"]), r["root_targets"], r["k"], r["tW"], r["free"],
                 r["forced_extra"], r["n_leaves"], ",".join(r["mobile"])))
    wm = info["whole_mobile"]
    print("  whole mobile part: k=%d tW=%d free=%d forced_extra=%d leaves=%d" % (wm["k"], wm["tW"], wm["free"], wm["forced_extra"], wm["n_leaves"]))
    return order, info


# ------------------------------------------------------------------ instances
def key(cid, W, pool):
    return cid + ":" + pool + ":" + hashlib.sha256(json.dumps(sorted(W)).encode()).hexdigest()[:16]


def prior_mine():
    best = {}
    if os.path.exists(RES):
        for line in open(RES):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            k = key(r["circuit"], r["W"], r.get("pool", "full"))
            cur = best.get(k)
            if cur is None or r["result"] in ("UNSAT", "SAT") or (r["result"] == "TIMEOUT" and r["limit"] > cur[1]):
                best[k] = (r["result"], r.get("limit", 0))
    return best


def prior_sat():
    """Prior results of the sat/ campaigns (read only) for the same (circuit, W), full pool."""
    import batch2_driver
    return batch2_driver.prior()


def solve(K, m, limit, allowed=None, tag=""):
    req = {"K": sorted(K), "m": m, "solver": "cadical195", "distinct": True, "symbreak": True,
           "allowed": sorted(allowed) if allowed is not None else None}
    tmp = os.path.join(HERE, "tmp_req.json")
    json.dump(req, open(tmp, "w"))
    t0 = time.time()
    try:
        p = subprocess.run(["nice", "-n", str(NICE), "python3", os.path.join(HERE, "solve_child.py"), tmp],
                           capture_output=True, text=True, timeout=limit + 5)
        out = p.stdout.strip().splitlines()
        res = json.loads(out[-1]) if out else {"result": "ERROR", "err": p.stderr[-800:]}
    except subprocess.TimeoutExpired:
        res = {"result": "TIMEOUT"}
    res["secs"] = round(time.time() - t0, 1); res["limit"] = limit; res["tag"] = tag
    return res


def unit_vector_ok(full):
    for j in range(32):
        val = {1 << i: int(i == j) for i in range(32)}
        for v, a, b in full:
            val[v] = val[a] ^ val[b]
        for t in sat87.TARGETS:
            if val.get(t) != (t >> j) & 1:
                return False
    return True


def items_for(order, comps, levels):
    n = len(comps)
    its = []
    for lv in levels:
        if lv == "all":
            its.append(list(range(n)))
        else:
            for c in itertools.combinations(range(n), int(lv)):
                its.append(list(c))
    out, seen = [], {}
    for idxs in its:
        name, W, desc, tW = describe(order, comps, idxs)
        if W in seen:
            seen[W]["desc"]["same_W_as"] = seen[W]["desc"].get("same_W_as", []) + [name]
            continue
        rec = {"name": name, "W": W, "desc": desc, "tW": tW, "level": "all" if len(idxs) == n and "all" in levels and len(idxs) > 3 else len(idxs)}
        seen[W] = rec; out.append(rec)
    out.sort(key=lambda r: (len(r["W"]) - r["tW"], len(r["W"]), r["name"]))
    return out


def run(cid, levels, limit, pool="full"):
    order, info = analyze(cid, write=True)
    comps = info["components"]
    vals = sat87.values_of(order)
    items = items_for(order, comps, levels)
    mine = prior_mine()
    try:
        psat = prior_sat()
    except Exception as e:
        log("prior_sat failed: %s" % e); psat = {}
    log("run %s levels=%s limit=%d pool=%s: %d instances (k histogram %s)"
        % (cid, levels, limit, pool, len(items), sorted(collections.Counter(len(r["W"]) for r in items).items())))
    for rec in items:
        if os.path.exists(STOP):
            log("STOP present"); return
        W = rec["W"]; name = rec["name"]
        kk = key(cid, W, pool)
        b = mine.get(kk)
        if b is not None and (b[0] in ("UNSAT", "SAT") or (b[0] == "TIMEOUT" and b[1] >= limit)):
            continue
        K = [v for v in vals if v not in W]
        assert sat87.split_closed(K)
        k = len(W); tW = rec["tW"]
        allowed = None
        if pool == "span":
            basis = span_basis(rec["desc"]["leaves"])
            allowed = [v for v in sat87.INPUTS + K if in_span(basis, v)]
        r = solve(K, k - 1, limit, allowed, tag=name)
        pk = cid + ":" + hashlib.sha256(json.dumps(sorted(W)).encode()).hexdigest()[:16]
        row = {"circuit": cid, "depth": info["depth"], "scope": name, "k": k, "targets_in_W": tW, "W": sorted(W),
               "result": r.get("result"), "secs": r.get("secs"), "solve_secs": r.get("solve_secs"),
               "nvars": r.get("nvars"), "nclauses": r.get("nclauses"), "limit": limit, "distinct": True,
               "family": "M", "level": rec["level"], "pool": pool, "n_allowed": (len(allowed) if allowed else None),
               "component": {kx: vx for kx, vx in rec["desc"].items() if kx != "leaves"},
               "leaves": ["%08x" % v for v in rec["desc"]["leaves"]],
               "prior_sat_campaign": list(psat[pk]) if pk in psat else None,
               "time": time.strftime("%Y-%m-%dT%H:%M:%S")}
        if r.get("result") == "ERROR":
            row["err"] = r.get("err")
        if r.get("result") == "SAT":
            new = [tuple(x) for x in r["new_gates"]]
            full = [(v, a, b) for v, a, b in order if v in set(K)] + new
            chk = sat87.check_circuit(full)
            uv = unit_vector_ok(full)
            row["found"] = chk; row["full"] = full; row["unit_vectors_ok"] = uv
            h = hashlib.sha256(json.dumps(full).encode()).hexdigest()[:12]
            fpath = os.path.join(HERE, "found", "found_%s.json" % h)
            json.dump({"circuit": cid, "scope": name, "pool": pool, "order": full}, open(fpath, "w"))
            ver = subprocess.run(["python3", os.path.join(SAT, "write_circ.py"), fpath], capture_output=True, text=True)
            row["verify"] = ver.stdout + ver.stderr
            with open(FOUND, "a") as f:
                f.write("%s %s %s pool=%s check=%s unit_vectors=%s\n%s\n" % (time.strftime("%Y-%m-%dT%H:%M:%S"), cid, name, pool, chk, uv, ver.stdout))
            log("!!!!! SAT %s %s k=%d pool=%s -> circuit %s unit_vectors=%s; verification:\n%s" % (cid, name, k, pool, chk, uv, ver.stdout))
        with open(RES, "a") as f:
            f.write(json.dumps(row) + "\n")
        mine[kk] = (row["result"], limit)
        log("%-14s %-22s lvl=%-3s k=%2d tW=%2d free=%d pool=%-4s %-8s %7.1fs (solve %s) cl=%s prior=%s"
            % (cid, name, rec["level"], k, tW, k - 1 - tW, pool, row["result"], r.get("secs") or 0,
               r.get("solve_secs"), r.get("nclauses"), row["prior_sat_campaign"]))
    log("run complete %s" % cid)


if __name__ == "__main__":
    if sys.argv[1] == "analyze":
        analyze(sys.argv[2])
    elif sys.argv[1] == "run":
        cid = sys.argv[2]; levels = sys.argv[3].split(","); limit = int(sys.argv[4])
        pool = sys.argv[5] if len(sys.argv) > 5 else "full"
        run(cid, levels, limit, pool)
