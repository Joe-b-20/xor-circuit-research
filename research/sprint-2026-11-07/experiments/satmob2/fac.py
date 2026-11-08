"""satmob2/fac.py -- the COUPLED-factor instance: the window is the plateau's coupled factor itself
(its choice at the member state S, from the compressed plateau object), not a local fan component.

  python3 fac.py analyze CID PLSPEC            choices per factor at S, coupled factor's window sizes
  python3 fac.py run CID PLSPEC LIMIT [FIDX] [pool]   run the factor instance(s) (default FIDX = 0, the coupled one)
PLSPEC: kste:<index into kste/data/kste_plateau_objs.json> | hunt:<key in hunt/plateaus.json> | file:<path>

Plateau object (pes_lib.compress): core = helpers common to all members; factors = list of {values,
choices}; a member's helper set = core u one choice per factor (all modulo byte rotation).  The
instance for factor f at S: seeds = choice_f(S) u every value of S that uses a choice value as an
operand (under the greedy wiring), W = any-pair forced closure of the seeds (run_scopes.window with
ANYPAIR), K = S \\ W, instance I(K, |W| - 1) of sat87 -- identical in meaning to satmob's level-1
instance, with the plateau factor in place of the fan component.  UNSAT: no <= 87 circuit of any
depth contains K, i.e. no 87 keeps the core and the other factors' choices and redoes the coupled
factor (any values, any re-sharing with the kept values) in one gate less.
"""
import sys, os, json, time, hashlib, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mob2  # noqa: E402
from mob2 import sat87, run_scopes, log, solve, key, prior_mine, unit_vector_ok, RES, FOUND  # noqa: E402

SPRINT = mob2.SPRINT


def load_plateau(spec):
    kind, arg = spec.split(":", 1)
    if kind == "kste":
        p = json.load(open(os.path.join(SPRINT, "kste/data/kste_plateau_objs.json")))[int(arg)]
    elif kind == "hunt":
        p = json.load(open(os.path.join(SPRINT, "hunt/plateaus.json")))["plateaus"][arg]["plateau"]
    elif kind == "file":
        p = json.load(open(arg))
        p = p.get("plateau", p)
    else:
        raise ValueError(spec)
    return p


def rot(v, s):
    """rotate the 4 bytes of a 32-bit mask by s bytes"""
    s %= 4
    return ((v << (8 * s)) | (v >> (32 - 8 * s))) & 0xFFFFFFFF if s else v


def align(order, p):
    """Find the byte rotation s with rot(core, s) <= S; return s and the choice of every factor at S."""
    S = set(sat87.values_of(order))
    for s in range(4):
        core = {rot(v, s) for v in p["core"]}
        if core <= S:
            choices = []
            for f in p["factors"]:
                fv = {rot(v, s) for v in f["values"]}
                ch = sorted(S & fv)
                ok = any(sorted(rot(v, s) for v in c) == ch for c in f["choices"])
                choices.append({"choice": ch, "is_listed_choice": ok, "radix": len(f["choices"]),
                                "n_values": len(f["values"])})
            return s, core, choices
    raise RuntimeError("state is not a member of the plateau under any rotation")


def factor_window(order, choice):
    users = sat87.dependents(order)
    seeds = set(choice)
    roots = set()
    for m in choice:
        roots |= users[m]
    seeds |= roots
    W = frozenset(run_scopes.window(order, sorted(seeds)))
    tW = sum(1 for t in sat87.TARGETS if t in W)
    return W, tW, sorted(roots - set(choice))


def analyze(cid, spec, info=None):
    order = mob2.load(cid)
    p = load_plateau(spec)
    s, core, choices = align(order, p)
    S = set(sat87.values_of(order))
    helpers = {v for v in S if v not in sat87.TSET}
    tot = len(core) + sum(len(c["choice"]) for c in choices)
    assert tot == len(helpers) == 56, (tot, len(helpers))
    assert all(c["is_listed_choice"] for c in choices), [c["is_listed_choice"] for c in choices]
    # local fan structure for comparison
    comp = json.load(open(os.path.join(HERE, "comp_%s.json" % cid.replace(":", "_"))))
    loc_mobile = set(comp["fan"]["mobile"])
    out = {"circuit": cid, "plateau": spec, "rotation": s, "plateau_core": len(core),
           "local_core": len(comp["fan"]["core"]), "local_mobile": len(loc_mobile), "factors": []}
    print("circuit %s plateau %s (rotation %d): plateau core %d, local core %d, local mobile %d, factor shapes %s"
          % (cid, spec, s, len(core), len(comp["fan"]["core"]), len(loc_mobile), [c["radix"] for c in choices]))
    for i, c in enumerate(choices):
        W, tW, roots = factor_window(order, c["choice"])
        ch = set(c["choice"])
        inv = sorted(ch - loc_mobile)      # choice values the local fan does not move at S
        # which local components contain the choice's mobile values
        cids = [j for j, cc in enumerate(comp["components"]) if set(cc["mobile"]) & ch]
        row = {"idx": i, "radix": c["radix"], "n_factor_values": c["n_values"], "choice": ["%08x" % v for v in c["choice"]],
               "choice_locally_core": ["%08x" % v for v in inv], "local_components": cids,
               "roots": ["%08x" % v for v in roots], "root_targets": sum(1 for r in roots if r in sat87.TSET),
               "k": len(W), "tW": tW, "free": len(W) - 1 - tW, "forced_extra": len(W) - len(ch) - len(roots),
               "W": sorted(W)}
        out["factors"].append(row)
        print("  f%d radix %-5d choice %2d values (locally core: %d)  local comps %-14s roots %d (targets %d)  k=%2d tW=%2d free=%2d forced_extra=%d"
              % (i, c["radix"], len(ch), len(inv), cids, len(roots), row["root_targets"], len(W), tW, row["free"], row["forced_extra"]))
    json.dump(out, open(os.path.join(HERE, "fac_%s.json" % cid.replace(":", "_")), "w"), indent=1)
    sys.stdout.flush()
    return order, out


def run(cid, spec, limit, fidx=(0,), pool="full"):
    order, info = analyze(cid, spec)
    vals = sat87.values_of(order)
    mine = prior_mine()
    for i in fidx:
        if os.path.exists(mob2.STOP):
            log("STOP present"); return
        row0 = info["factors"][i]
        W = frozenset(row0["W"]); name = "F:f%d(r%d)" % (i, row0["radix"])
        kk = key(cid, W, pool)
        b = mine.get(kk)
        if b is not None and (b[0] in ("UNSAT", "SAT") or (b[0] == "TIMEOUT" and b[1] >= limit)):
            log("skip %s %s (prior %s)" % (cid, name, b)); continue
        K = [v for v in vals if v not in W]
        assert sat87.split_closed(K)
        k = len(W); tW = row0["tW"]
        allowed = None
        if pool == "span":
            lv = mob2.leaves(order, W)
            basis = mob2.span_basis(lv)
            allowed = [v for v in sat87.INPUTS + K if mob2.in_span(basis, v)]
        r = solve(K, k - 1, limit, allowed, tag=name)
        row = {"circuit": cid, "depth": info.get("depth"), "scope": name, "k": k, "targets_in_W": tW, "W": sorted(W),
               "result": r.get("result"), "secs": r.get("secs"), "solve_secs": r.get("solve_secs"),
               "nvars": r.get("nvars"), "nclauses": r.get("nclauses"), "limit": limit, "distinct": True,
               "family": "F", "level": "factor", "pool": pool, "n_allowed": (len(allowed) if allowed else None),
               "plateau": spec, "factor": {kx: vx for kx, vx in row0.items() if kx != "W"},
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
            import subprocess
            ver = subprocess.run(["python3", os.path.join(mob2.SAT, "write_circ.py"), fpath], capture_output=True, text=True)
            row["verify"] = ver.stdout + ver.stderr
            with open(FOUND, "a") as f:
                f.write("%s %s %s pool=%s check=%s unit_vectors=%s\n%s\n" % (time.strftime("%Y-%m-%dT%H:%M:%S"), cid, name, pool, chk, uv, ver.stdout))
            log("!!!!! SAT %s %s k=%d pool=%s -> circuit %s unit_vectors=%s; verification:\n%s" % (cid, name, k, pool, chk, uv, ver.stdout))
        with open(RES, "a") as f:
            f.write(json.dumps(row) + "\n")
        mine[kk] = (row["result"], limit)
        log("%-14s %-22s lvl=fac k=%2d tW=%2d free=%d pool=%-4s %-8s %7.1fs (solve %s) cl=%s"
            % (cid, name, k, tW, k - 1 - tW, pool, row["result"], r.get("secs") or 0, r.get("solve_secs"), r.get("nclauses")))


if __name__ == "__main__":
    if sys.argv[1] == "analyze":
        analyze(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "run":
        cid, spec, limit = sys.argv[2], sys.argv[3], int(sys.argv[4])
        fidx = tuple(int(x) for x in sys.argv[5].split(",")) if len(sys.argv) > 5 else (0,)
        pool = sys.argv[6] if len(sys.argv) > 6 else "full"
        run(cid, spec, limit, fidx, pool)
