#!/usr/bin/env python3
"""Power control for the sprint's SAT window refutations: anchors one gate above a known improvement.

Part 1 (no solver): build the anchor set, enumerate EXACTLY the sprint's windows (run_scopes.scopes:
family A one-seed k <= 10, family C output blocks k <= 12, family B two-seed k <= 9), and for each
window decide whether its kept set K is contained in a known improved circuit (then I(K, k-1) is SAT
by the sat87 claim; otherwise no window of this family can find THAT improvement).  Also the value-set
distance between every anchor and its improvement.  Writes anchors.json, windows.json, part1.txt.
Read-only everywhere except this folder.  Usage: nice -n 8 python3 anchors.py
"""
import sys, os, json, glob, collections, time, hashlib
H = os.path.expanduser("~")
S = H + "/xs-campaigns/2026-11-07-sprint"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, S + "/sat")
import sat87, run_scopes  # noqa: E402

N = 32
INPUTSET = set(sat87.INPUTS)
TSET = sat87.TSET
REPO = H + "/xor-circuit-research/circuits/aes-mixcolumns"
T0 = time.time()


def log(*a):
    msg = "[%6.0fs] " % (time.time() - T0) + " ".join(str(x) for x in a)
    print(msg); sys.stdout.flush()
    with open(os.path.join(HERE, "part1.txt"), "a") as f:
        f.write(msg + "\n")


def helpers(vals):
    return frozenset(v for v in vals if v not in TSET and v not in INPUTSET)


def rotset(vs, s):
    return frozenset(sat87.rot(v, s) for v in vs)


def vkey(vals):
    return hashlib.sha256(json.dumps(sorted(vals)).encode()).hexdigest()[:16]


def dist_stats(anchor_vals, imp_vals):
    """(k_needed, symdiff) in the identity frame and the minimum over the 4 byte rotations, helpers only."""
    a = helpers(anchor_vals)
    out = {}
    for s in range(4):
        b = rotset(helpers(imp_vals), s)
        need = len(a - b)
        sd = len(a ^ b)
        if s == 0:
            out["need0"], out["sd0"] = need, sd
        if "need_min" not in out or (need, sd) < (out["need_min"], out["sd_min"]):
            out["need_min"], out["sd_min"], out["rot_min"] = need, sd, s
    return out


# ------------------------------------------------------------------ 1. hunt 89 -> 88 pairs
def restart_times(runs):
    out = {}
    if not os.path.isdir(runs):
        return out
    for arm in sorted(os.listdir(runs)):
        wdir = os.path.join(runs, arm, "workers")
        if not os.path.isdir(wdir):
            continue
        for w in sorted(os.listdir(wdir)):
            p = os.path.join(wdir, w, "events.jsonl")
            if not os.path.exists(p):
                continue
            ts = []
            for line in open(p):
                if '"restart"' not in line:
                    continue
                try:
                    e = json.loads(line)
                except Exception:
                    continue
                if e.get("ev") == "restart":
                    ts.append(e["t"])
            out[(arm, w)] = sorted(ts)
    return out


def chain_index(rt, arm, w, t):
    ts = rt.get((arm, w), [])
    i = 0
    while i < len(ts) and ts[i] <= t:
        i += 1
    return i


SRC = [("sampleA", "hunt/samples.jsonl", "hunt/runs", {"A", "B"}),
       ("sampleC", "hunt/samplesC/samples.jsonl", "hunt/runs", {"C"}),
       ("sampleD", "hunt/samplesD/samples.jsonl", "hunt/runsD", {"D0", "D4", "DN"})]


def hunt_pairs():
    rts = {}
    chains = collections.defaultdict(list)
    all88 = {}
    for tag, rel, runs, arms in SRC:
        if runs not in rts:
            rts[runs] = restart_times(os.path.join(S, runs))
        for i, line in enumerate(open(os.path.join(S, rel))):
            r = json.loads(line)
            if r["arm"] not in arms:
                continue
            r["id"] = "%s:%d" % (tag, i)
            c = chain_index(rts[runs], r["arm"], r["worker"], r["t"] or 0)
            chains[(tag, r["arm"], r["worker"], c)].append(r)
            if r["gates"] == 88:
                all88[r["hash"]] = r["values"]
    pairs = []
    for ck, rs in sorted(chains.items()):
        rs.sort(key=lambda r: r["wall"])
        seen88 = False
        last89 = None
        n89 = 0
        for r in rs:
            if r["gates"] == 89:
                last89 = r
                n89 += 1
            elif r["gates"] == 88:
                if last89 is not None:
                    pairs.append({"chain": list(ck), "a89": last89, "b88": r, "kind": "excursion" if seen88 else "descent",
                                  "gap_wall": r["wall"] - last89["wall"],
                                  "gap_steps": (r["steps"] - last89["steps"]) if (r["steps"] is not None and last89["steps"] is not None) else None,
                                  "n89_before": n89})
                seen88 = True
                last89 = None
                n89 = 0
    log("hunt: chains with samples %d; 89->88 pairs %d (descent %d, excursion %d); distinct 88 states %d"
        % (len(chains), len(pairs), sum(p["kind"] == "descent" for p in pairs), sum(p["kind"] == "excursion" for p in pairs), len(all88)))
    return pairs, all88


# ------------------------------------------------------------------ 2. corpora of known smaller circuits
def load_rec_values(path):
    try:
        return sat87.values_of(sat87.load_record(path))
    except Exception:
        return None


def corpus88(all88):
    """All known 88 value sets: hunt samples, mc87 records (all workers), kste value sets, repo 88."""
    C = {}
    for h, v in all88.items():
        C["hunt:" + h] = v
    for f in glob.glob(H + "/xs-campaigns/2026-11-04-mc87/runs/mc87/workers/*/records/g88-*.json"):
        if f.endswith("verification.json"):
            continue
        v = load_rec_values(f)
        if v and len(v) == 88:
            C["mc87:" + os.path.basename(os.path.dirname(os.path.dirname(f))) + ":" + os.path.basename(f)[:20]] = v
    ks = json.load(open(S + "/kste/data/kste_valuesets.json"))
    for i, v in enumerate(ks):
        if len(v) == 88:
            C["kste:%d" % i] = v
    C["repo88"] = sat87.values_of(sat87.load_repo_circ())
    return C


def main():
    open(os.path.join(HERE, "part1.txt"), "w").close()
    pairs, all88 = hunt_pairs()
    # distance distribution over ALL pairs
    dd = []
    for p in pairs:
        d = dist_stats(p["a89"]["values"], p["b88"]["values"])
        p["dist"] = d
        dd.append(d)
    def q(xs):
        xs = sorted(xs); n = len(xs)
        return "n=%d min=%d q1=%d med=%d q3=%d max=%d" % (n, xs[0], xs[n // 4], xs[n // 2], xs[3 * n // 4], xs[-1]) if xs else "-"
    for kind in ("descent", "excursion"):
        sel = [p["dist"] for p in pairs if p["kind"] == kind]
        log("all %s pairs: k_needed=|H89\\H88| (identity frame): %s" % (kind, q([d["need0"] for d in sel])))
        log("all %s pairs: |H89 xor H88| (identity frame): %s" % (kind, q([d["sd0"] for d in sel])))
        log("all %s pairs: k_needed min over rotations: %s" % (kind, q([d["need_min"] for d in sel])))
    hist = collections.Counter(min(d["need0"], 30) for d in dd)
    log("k_needed histogram (all pairs, identity frame; 30 = >= 30): %s" % sorted(hist.items()))
    gaps = [p["gap_wall"] for p in pairs]
    log("sample gap 89->88 wall seconds: %s" % q(gaps))

    # choose anchors: descent pairs first, round robin over arms, one per chain, distinct 89 states
    chosen = []
    used_chain, used_hash = set(), set()
    by_arm = collections.defaultdict(list)
    for p in pairs:
        if p["kind"] == "descent":
            by_arm[p["chain"][1]].append(p)
    for arm in by_arm:
        by_arm[arm].sort(key=lambda p: p["gap_wall"])   # tightest sample gap first
    arms = sorted(by_arm)
    while len(chosen) < 20 and any(by_arm.values()):
        for arm in arms:
            while by_arm[arm]:
                p = by_arm[arm].pop(0)
                ck = tuple(p["chain"])
                if ck in used_chain or p["a89"]["hash"] in used_hash:
                    continue
                if sat87.wiring_from_values(p["a89"]["values"]) is None or sat87.wiring_from_values(p["b88"]["values"]) is None:
                    continue
                chosen.append(p); used_chain.add(ck); used_hash.add(p["a89"]["hash"])
                break
            if len(chosen) >= 20:
                break
    exc = sorted([p for p in pairs if p["kind"] == "excursion"], key=lambda p: p["gap_wall"])
    n_exc = 0
    for p in exc:
        if n_exc >= 5:
            break
        if p["a89"]["hash"] in used_hash or tuple(p["chain"]) in used_chain:
            continue
        if sat87.wiring_from_values(p["a89"]["values"]) is None:
            continue
        chosen.append(p); used_hash.add(p["a89"]["hash"]); used_chain.add(tuple(p["chain"])); n_exc += 1
    log("chosen hunt anchors: %d (%d descent, %d excursion)" % (len(chosen), len(chosen) - n_exc, n_exc))

    anchors = []
    for p in chosen:
        anchors.append({"id": "hunt89:" + p["a89"]["id"], "kind": "hunt-" + p["kind"], "gates": 89,
                        "values": p["a89"]["values"], "chain": p["chain"], "gap_wall": round(p["gap_wall"], 1),
                        "gap_steps": p["gap_steps"],
                        "truth": {"id": p["b88"]["id"], "values": p["b88"]["values"]}, "dist": p["dist"]})

    # repo / seed anchors
    log("loading corpora")
    C88 = corpus88(all88)
    s89 = json.load(open(S + "/q89check/c1_states_89.json"))["states"]
    s90 = json.load(open(S + "/q89check/c1_states_90.json"))["states"]
    fam89 = {}
    for st in s89:
        v = sorted(set(st["helpers"]) | TSET)
        if len(v) == 89 and sat87.wiring_from_values(v) is not None:
            fam89[vkey(v)] = v
    st90 = {}
    for st in s90:
        v = sorted(set(st["helpers"]) | TSET)
        if len(v) == 90:
            st90[vkey(v)] = v
    log("corpus: 88s %d (hunt %d, mc87 %d, kste %d); 89@4 states %d; 90@4 states %d"
        % (len(C88), sum(k.startswith("hunt") for k in C88), sum(k.startswith("mc87") for k in C88),
           sum(k.startswith("kste") for k in C88), len(fam89), len(st90)))

    repo89 = sat87.values_of(sat87.load_repo_circ(REPO + "/aes-mixcolumns-xor89-depth4.circ.txt"))
    repo97 = sat87.values_of(sat87.load_repo_circ(REPO + "/aes-mixcolumns-xor97-depth3.circ.txt"))
    july91 = load_rec_values(H + "/xs-campaigns/2026-10-31-adopt/seeds/mc-july-g91-d4.json")
    nist90 = load_rec_values(H + "/xs-campaigns/2026-10-31-adopt/seeds/mc-nist-g90-d4.json")
    assert len(repo89) == 89 and len(repo97) == 97 and len(july91) == 91 and len(nist90) == 90, (len(repo89), len(repo97), len(july91), len(nist90))
    from89 = {}
    for f in glob.glob(H + "/xs-campaigns/2026-11-04-mc87/runs/mc87/workers/from89-*/records/g88-*.json"):
        if f.endswith("verification.json"):
            continue
        v = load_rec_values(f)
        if v and len(v) == 88:
            from89[vkey(v)] = v
    log("from89 workers' distinct 88s: %d" % len(from89))
    # 90@4 states with the 89's exact first layer (q89check P2 population), improvement = the 89@4 family
    L1 = frozenset(v for v in helpers(repo89) if bin(v).count("1") == 2)
    p2 = {k: v for k, v in st90.items() if frozenset(x for x in helpers(v) if bin(x).count("1") == 2) == L1}
    log("90@4 states with the 89's first layer: %d" % len(p2))

    def best_imp(anchor_vals, imps):
        """closest improvement (min k_needed over members and rotations) and the whole distribution."""
        best = None
        needs = []
        for name, v in imps.items():
            d = dist_stats(anchor_vals, v)
            needs.append(d["need_min"])
            if best is None or (d["need_min"], d["sd_min"]) < (best[1]["need_min"], best[1]["sd_min"]):
                best = (name, d)
        return best, needs

    allsmaller = dict(C88); allsmaller.update({"fam89:" + k: v for k, v in fam89.items()})
    allsmaller90 = dict(allsmaller); allsmaller90.update({"st90:" + k: v for k, v in st90.items()})
    allsmaller90.update({"july91": july91})
    specs = [("repo89@4", "repo", repo89, {"from89:" + k: v for k, v in from89.items()}, "88s reached by the mc87 from89 workers seeded with it"),
             ("repo89@4/any88", "repo", repo89, C88, "any known 88"),
             ("july91@4", "seed", july91, {"fam89:" + k: v for k, v in fam89.items()}, "the 89@4 family it descended to (v8 control, 914 s)"),
             ("nist90@4", "seed", nist90, allsmaller, "any known 88 or 89@4 (no logged descent exists)"),
             ("repo97@3", "repo", repo97, allsmaller90, "any known 88, 89@4, 90@4 or the July 91@4")]
    for aid, kind, vals, imps, note in specs:
        best, needs = best_imp(vals, imps)
        hist = collections.Counter(min(x, 40) for x in needs)
        log("%s vs %s (%d circuits): closest %s need_min=%d sd_min=%d rot=%d; k_needed histogram %s"
            % (aid, note, len(imps), best[0], best[1]["need_min"], best[1]["sd_min"], best[1]["rot_min"], sorted(hist.items())[:12]))
        if aid.endswith("/any88"):
            continue
        anchors.append({"id": aid, "kind": kind, "gates": len(vals), "values": vals, "truth": {"id": best[0], "values": imps[best[0]]},
                        "dist": best[1], "imp_note": note, "n_imps": len(imps),
                        "need_hist": sorted(hist.items())})
    # P2 90@4 anchors: those closest to the family
    p2rows = []
    for k, v in p2.items():
        best, needs = best_imp(v, {"fam89:" + kk: vv for kk, vv in fam89.items()})
        p2rows.append((best[1]["need_min"], k, best))
    p2rows.sort()
    log("P2 90@4 anchors, k_needed to the nearest 89@4 family member: %s" % [r[0] for r in p2rows])
    for need, k, best in p2rows[:6]:
        anchors.append({"id": "p2_90@4:" + k, "kind": "p2", "gates": 90, "values": p2[k], "truth": {"id": best[0], "values": fam89[best[0][6:]]},
                        "dist": best[1], "imp_note": "nearest 89@4 family member"})

    # ------------------------------------------------------------------ windows + containment
    log("enumerating windows (sprint generators) for %d anchors" % len(anchors))
    win_out = []
    for a in anchors:
        vals = a["values"]
        order = sat87.wiring_from_values(vals)
        assert order is not None
        g, d, nd = sat87.check_circuit(order)
        assert g == a["gates"] and nd == g
        a["depth_anypair"] = d
        ah = helpers(vals)
        truth = a["truth"]["values"]
        # missing sets per rotation of the truth, and per corpus member with |M| <= 12
        Mtruth = [ah - rotset(helpers(truth), s) for s in range(4)]
        Mcorp = []
        pool = {}
        if a["gates"] == 89:
            pool = C88
        elif a["gates"] == 90:
            pool = allsmaller
        elif a["gates"] == 91:
            pool = dict(allsmaller, **{"st90:" + k: v for k, v in st90.items()})
        else:
            pool = allsmaller90
        for name, v in pool.items():
            hv = helpers(v)
            for s in range(4):
                M = ah - rotset(hv, s)
                if len(M) <= 12:
                    Mcorp.append((name, s, M))
        a["n_corpus_within12"] = len(Mcorp)
        fams = [("A", 10), ("C", 12), ("B", 9)]
        seen = set()
        rows = []
        for fam, kmax in fams:
            t1 = time.time()
            sc = run_scopes.scopes(order, fam, None)
            for name, W in sc:
                k = len(W)
                if k > kmax or W in seen:
                    continue
                seen.add(W)
                Wh = frozenset(W) - TSET
                tw = sum(1 for t in sat87.TARGETS if t in W)
                cont_truth = any(M <= Wh for M in Mtruth)
                cont_corp = [(n, s) for n, s, M in Mcorp if M <= Wh]
                rows.append({"anchor": a["id"], "scope": name, "fam": fam, "k": k, "tW": tw, "free": k - 1 - tw,
                             "W": sorted(W), "contained_truth": cont_truth, "n_contained_corpus": len(cont_corp),
                             "contained_corpus_example": cont_corp[0] if cont_corp else None})
            a["n_%s" % fam] = sum(1 for r in rows if r["fam"] == fam)
            a["sec_%s" % fam] = round(time.time() - t1, 1)
        a["n_windows"] = len(rows)
        a["n_contained_truth"] = sum(r["contained_truth"] for r in rows)
        a["n_contained_corpus"] = sum(1 for r in rows if r["n_contained_corpus"])
        a["kmax_A"] = max([r["k"] for r in rows if r["fam"] == "A"] or [0])
        win_out += rows
        log("%-28s %s g=%d need0=%d sd0=%d need_min=%d | windows A=%d C=%d B=%d | contained(truth)=%d contained(any known)=%d | corpus members within 12: %d"
            % (a["id"], a["kind"], a["gates"], a["dist"]["need0"], a["dist"]["sd0"], a["dist"]["need_min"], a["n_A"], a["n_C"], a["n_B"],
               a["n_contained_truth"], a["n_contained_corpus"], a["n_corpus_within12"]))
    json.dump(anchors, open(os.path.join(HERE, "anchors.json"), "w"))
    json.dump(win_out, open(os.path.join(HERE, "windows.json"), "w"))
    json.dump([{k: v for k, v in p.items() if k not in ("a89", "b88")} | {"a89": p["a89"]["id"], "b88": p["b88"]["id"], "a89_hash": p["a89"]["hash"]}
               for p in pairs], open(os.path.join(HERE, "pairs.json"), "w"))
    tot = len(win_out)
    log("TOTAL windows %d; contained in truth %d; contained in any known smaller circuit %d; anchors with >= 1 truth-contained window: %d of %d"
        % (tot, sum(r["contained_truth"] for r in win_out), sum(1 for r in win_out if r["n_contained_corpus"]),
           sum(1 for a in anchors if a["n_contained_truth"]), len(anchors)))


if __name__ == "__main__":
    main()
