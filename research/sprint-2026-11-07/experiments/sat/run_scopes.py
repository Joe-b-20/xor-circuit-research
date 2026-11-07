"""Scope driver.  usage: python3 run_scopes.py CIRCUIT FAMILY KMIN KMAX LIMIT MAXINST [distinct=1]
CIRCUIT: repo | sampleA:<line> | sampleC:<line> | rec:<path>
FAMILY:  A (one seed value: upward closure + dead cone), B (two seeds), C (byte block: the 8
         outputs of byte b, b=0..3), D (mobile part from mobile_<id>.json: S minus plateau core),
         R (random windows: random seed sets of size 2-3)
Appends one json line per instance to results.jsonl and prints a table row."""
import sys, os, json, time, random, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sat87

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results.jsonl")
CID = []
ANYPAIR = os.environ.get("ANYPAIR", "0") == "1"


def load(cid):
    if cid == "repo":
        return sat87.load_repo_circ()
    if cid.startswith("sample"):
        which, line = cid.split(":")
        path = os.path.join(sat87.SPRINT, "hunt", "samples.jsonl" if which == "sampleA" else "samplesC/samples.jsonl")
        d = json.loads(open(path).read().splitlines()[int(line)])
        assert d["gates"] == 88
        order = sat87.wiring_from_values(d["values"])
        assert order is not None
        return order
    if cid.startswith("rec:"):
        return sat87.load_record(cid[4:])
    raise ValueError(cid)


def window(order, seeds):
    """W = upward closure of seeds (under the wiring), then dead helpers, then whatever K still
    cannot compute (split-closure under any pair).  Returns W (set)."""
    vals = sat87.values_of(order)
    if ANYPAIR:
        # minimal forced removal: only what K cannot recompute from any pair
        W = set(seeds)
    else:
        W = sat87.closure_remove(order, seeds)
    W = sat87.private_cone(order, W)
    K = [v for v in vals if v not in W]
    # make K split-closed under any pair
    while True:
        wr = sat87.wiring_from_values(K)
        if wr is not None:
            break
        comp = set(sat87.values_of(sat87.wiring_from_values_partial(K)))
        K = [v for v in K if v in comp]
    W = set(vals) - set(K)
    return W


def scopes(order, family, rng):
    vals = sat87.values_of(order)
    out = []
    if family == "A":
        seen = set()
        for v in vals:
            W = frozenset(window(order, [v]))
            if W in seen:
                continue
            seen.add(W)
            out.append(("A:v=%08x" % v, W))
    elif family == "B":
        seen = set()
        singles = [(v, frozenset(window(order, [v]))) for v in vals]
        for i in range(len(singles)):
            for j in range(i + 1, len(singles)):
                W = frozenset(window(order, [singles[i][0], singles[j][0]]))
                if W in seen or W == singles[i][1] or W == singles[j][1]:
                    continue
                seen.add(W)
                out.append(("B:v=%08x,%08x" % (singles[i][0], singles[j][0]), W))
    elif family == "C":
        for b in range(4):
            roots = [sat87.TARGETS[8 * b + r] for r in range(8)]
            out.append(("C:byte%d" % b, frozenset(window(order, roots))))
        for b in range(4):   # half bytes too
            for h in range(2):
                roots = [sat87.TARGETS[8 * b + r] for r in range(4 * h, 4 * h + 4)]
                out.append(("C:byte%d.half%d" % (b, h), frozenset(window(order, roots))))
    elif family in ("D", "D1"):
        info = {c["id"]: c for c in json.load(open(os.path.join(HERE, "circuits.json")))}
        c = info[CID[0]]
        mob = [v for v in c["mobile"]]
        W0 = frozenset(window(order, mob))
        out.append(("D:mobile(%d)" % len(mob), W0))
        if family == "D1":
            seen = {W0}
            for v in c["core"]:
                W = frozenset(window(order, mob + [v]))
                if W in seen:
                    continue
                seen.add(W)
                out.append(("D1:mobile+%08x" % v, W))
    elif family == "R":
        for _ in range(300):
            seeds = rng.sample(vals, rng.choice([2, 3, 3, 4]))
            out.append(("R:" + ",".join("%08x" % s for s in seeds), frozenset(window(order, seeds))))
    return out


def main():
    cid, family, kmin, kmax, limit, maxinst = sys.argv[1:7]
    kmin, kmax, limit, maxinst = int(kmin), int(kmax), float(limit), int(maxinst)
    distinct = (sys.argv[7] == "1") if len(sys.argv) > 7 else True
    CID.append(cid)
    order = load(cid)
    g, d, nd = sat87.check_circuit(order)
    assert g == 88 and nd == 88
    rng = random.Random(1)
    sc = scopes(order, family, rng)
    sc = [(name, W) for name, W in sc if kmin <= len(W) <= kmax]
    sc.sort(key=lambda x: len(x[1]))
    # dedupe by W
    seen, uniq = set(), []
    for name, W in sc:
        if W not in seen:
            seen.add(W); uniq.append((name, W))
    print("circuit %s depth %d family %s: %d scopes with k in [%d,%d]" % (cid, d, family, len(uniq), kmin, kmax))
    vals = sat87.values_of(order)
    done = 0
    for name, W in uniq:
        if done >= maxinst:
            break
        K = [v for v in vals if v not in W]
        assert sat87.split_closed(K)
        k = len(W)
        nt = sum(1 for t in sat87.TARGETS if t in W)
        r = sat87.solve_instance(K, k - 1, limit, distinct=distinct, tag=name)
        row = {"circuit": cid, "depth": d, "scope": name, "k": k, "targets_in_W": nt,
               "W": sorted(W), "result": r.get("result"), "secs": r.get("secs"),
               "solve_secs": r.get("solve_secs"), "nvars": r.get("nvars"), "nclauses": r.get("nclauses"),
               "limit": limit, "distinct": distinct, "time": time.strftime("%H:%M:%S")}
        if r.get("result") == "SAT":
            new = [tuple(x) for x in r["new_gates"]]
            full = [(v, a, b) for v, a, b in order if v in set(K)] + new
            chk = sat87.check_circuit(full)
            row["found"] = chk
            row["full"] = full
            print("!!!!! SAT: reconstructed circuit", chk)
            tagh = hashlib.sha256(json.dumps(full).encode()).hexdigest()[:12]
            json.dump({"circuit": cid, "scope": name, "order": full}, open(os.path.join(HERE, "found", "found_%s.json" % tagh), "w"))
        if r.get("result") == "ERROR":
            row["err"] = r.get("err")
        with open(RES, "a") as f:
            f.write(json.dumps(row) + "\n")
        print("%-22s %-28s k=%2d t=%d %-8s %6.1fs vars=%s cl=%s" % (cid, name, k, nt, row["result"], r.get("secs", 0), r.get("nvars"), r.get("nclauses")))
        sys.stdout.flush()
        done += 1


if __name__ == "__main__":
    main()
