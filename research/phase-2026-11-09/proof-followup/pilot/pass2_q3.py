#!/usr/bin/env python3
"""pass2_q3.py -- second pass of the pilot: the 9 leaves never run, the UNRESOLVED leaves, and every multi-segment skeleton
touched by the pass-1 product-phase bug (patch_20261111.py), with ONE geometric run per distinct skeleton (step G does not
depend on the key: a skeleton is (roles, statuses)).  Writes results_final/ (the FINAL per-leaf results of the pilot); the
pass-1 files in results/ are left untouched.

1. step S (LP monotone / exact, then R8-int MILP) is recomputed for all 207 leaves and compared with the pass-1 record;
2. a pass-1 geometric outcome is REUSED only if it is 'done' with 0 survivors and not affected by the bug: single-segment
   skeletons, or multi-segment skeletons without any r = 0, u >= 2 role, or multi-segment ones in which a segment had no
   realization (the segment enumeration was not affected);
3. every other distinct skeleton is run here (patched enum_q3.run_skeleton): round A with a short CPU cap, round B with a
   longer cap for what is left, within the CPU budget; a cap / timeout / error stays UNRESOLVED;
4. per leaf: SURVIVING if a skeleton has a realization whose completed witness passes verify_q3 (R1-R8) for this leaf;
   EXCLUDED if every skeleton is done with 0 survivors; UNRESOLVED otherwise.
usage: python3 pass2_q3.py [--workers 7] [--budget 5000] [--capA 20] [--capBmax 240]
"""
import sys, json, time, glob, argparse, itertools, os
from collections import Counter, defaultdict
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import enum_q3 as E, verify_q3 as V  # noqa: E402
OUT = HERE / "results_final"


def sig_of(roles, status): return json.dumps([roles, "".join(status)])


def step_s(task):
    key, a, d = task; c0 = time.process_time()
    lp = E.LeafLP(key, a, d)
    skels_lp, sstats = E.skeleton_enum(lp, a, d)
    skels = []; killed = []; hist = Counter()
    for sk in skels_lp:
        ms = V.milp_status(key, a, d, {tuple(int(x) for x in c.split(",")): n for c, n in sk["counts"].items()}, time_limit=20.0)
        hist[ms["status"]] += 1
        (killed if ms["status"] == 2 else skels).append(sk)
    return dict(key=list(key), A=a, qD=d, skeletons_lp=len(skels_lp), skeletons=skels, milp_killed=[sk["roles"] for sk in killed], milp_status_hist=dict(hist),
                skeleton_stats=dict(sstats), lp_calls=lp.ncalls, lp_status=dict(lp.status), lp_pruned_vectors=[[list(map(list, cv)), ex] for cv, ex in lp.pruned],
                cpu=round(time.process_time() - c0, 2))


def geom(task):
    sg, roles, status, cap = task; c0 = time.process_time()
    geo = E.build_geo()
    skel = dict(roles=roles, status=status, W=[sum(r for r, L in roles if s in L) for s in range(3)])
    pl = E.plan(skel, sym_first_root=True)
    try:
        res = E.run_skeleton(geo, pl, 6, 200, time.process_time() + cap, seg_cap=150_000)
    except MemoryError:
        res = dict(mode="?", survivors=0, snaps=[], stats={}, depth={}, deepest=[], status="capped", seg_counts=[])
    nodes = res["stats"].get("nodes", 0) + res["stats"].get("seg_nodes", 0) + res["stats"].get("prod_nodes", 0)
    return dict(sig=sg, roles=roles, status_slots=status, status=res["status"], survivors=res["survivors"], snaps=res["snaps"], stats=res["stats"], nodes=nodes,
                mode=res["mode"], seg_counts=res["seg_counts"], deepest=res["deepest"][:3], segments=len(pl["segments"]), cap=cap, cpu=round(time.process_time() - c0, 2))


def finalize(task):
    leaf, outcomes = task; c0 = time.process_time()
    geo = E.build_geo(); key = tuple(leaf["key"]); a = leaf["A"]; d = leaf["qD"]
    sl = []; witnesses = []; surv = 0; unresolved = []
    for sk in leaf["skeletons"]:
        o = outcomes[sig_of(sk["roles"], sk["status"])]
        e = dict(roles=sk["roles"], W=sk["W"], counts=sk["counts"], source=o["source"], status=o["status"], survivors=o["survivors"], nodes=o["nodes"],
                 mode=o.get("mode"), seg_counts=o.get("seg_counts"), geo_stats=o.get("stats"), cap=o.get("cap"), deepest_pruned=o.get("deepest"))
        if o["status"] == "done" and o["survivors"]:
            pl = E.plan(sk, sym_first_root=True); ok_w = 0
            for snap in o["snaps"][:5]:
                obj, rep = E.complete_witness(geo, pl, snap, key, a, d)
                w = dict(skeleton=sk["roles"], object=obj, verify={k: [v[0], v[1]] for k, v in rep.items() if isinstance(v, tuple)})
                if rep["all"][0]:
                    w["milp"] = V.milp_status(key, a, d, dict(V.counts_of(obj))); ok_w += 1
                witnesses.append(w)
            e["witnesses_verified"] = ok_w
            if ok_w: surv += o["survivors"]
            else: unresolved.append(dict(roles=sk["roles"], status="witness completion failed"))
        elif o["status"] != "done":
            unresolved.append(dict(roles=sk["roles"], status=o["status"]))
        sl.append(e)
    result = "SURVIVING" if surv else ("UNRESOLVED" if unresolved else "EXCLUDED")
    out = dict(key=leaf["key"], A=a, qD=d, skeletons_lp=leaf["skeletons_lp"], skeletons=len(leaf["skeletons"]), skeletons_milp_infeasible=len(leaf["milp_killed"]),
               skeletons_milp_killed=leaf["milp_killed"], milp_status_hist=leaf["milp_status_hist"], skeleton_stats=leaf["skeleton_stats"], lp_calls=leaf["lp_calls"],
               lp_status=leaf["lp_status"], lp_pruned_vectors=leaf["lp_pruned_vectors"], skeleton_list=sl, survivors=surv, witnesses=witnesses,
               unresolved_skeletons=unresolved, result=result, nodes=sum(e["nodes"] for e in sl),
               witness_verify_all=(all(w["verify"]["all"][0] for w in witnesses) if witnesses else None))
    if result == "EXCLUDED":
        out["excluded_by"] = "step S (LP)" if leaf["skeletons_lp"] == 0 else ("step S (LP + MILP)" if not leaf["skeletons"] else "step G (geometry)")
    out["finalize_cpu"] = round(time.process_time() - c0, 2)
    json.dump(out, open(OUT / ("leaf_%d_%d_%d_%d_a%d_d%d.json" % (key[0], key[1], key[2], key[5], a, d)), "w"))
    return {k: v for k, v in out.items() if k not in ("skeleton_list", "witnesses", "lp_pruned_vectors", "skeletons_milp_killed")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=7); ap.add_argument("--budget", type=float, default=5000.0)
    ap.add_argument("--capA", type=float, default=20.0); ap.add_argument("--capBmax", type=float, default=240.0)
    args = ap.parse_args()
    t0 = time.time(); OUT.mkdir(exist_ok=True)
    geo = E.build_geo()
    import multiprocessing as mp
    ctx = mp.get_context("fork")
    tasks = E.all_leaves()
    with ctx.Pool(args.workers) as pool:
        # ---- 1. step S for all leaves
        leaves = pool.map(step_s, tasks, chunksize=1)
        cpu_s = sum(l["cpu"] for l in leaves)
        print(f"step S: {len(leaves)} leaves, LP skeletons {sum(l['skeletons_lp'] for l in leaves)}, MILP-feasible {sum(len(l['skeletons']) for l in leaves)}, cpu {cpu_s:.0f}s", flush=True)
        # ---- 2. pass-1 outcomes
        p1 = defaultdict(list); mismatch = 0
        for fn in glob.glob(str(HERE / "results" / "leaf_*.json")):
            r = json.load(open(fn))
            lf = next(l for l in leaves if l["key"] == r["key"] and l["A"] == r["A"] and l["qD"] == r["qD"])
            if r["skeletons_lp"] != lf["skeletons_lp"] or r["skeletons"] != len(lf["skeletons"]): mismatch += 1
            status = E.slot_status(r["A"], r["qD"])
            for sk in r["skeleton_list"]:
                if "status" in sk: p1[sig_of(sk["roles"], status)].append(sk)
        print("pass-1 files:", len(glob.glob(str(HERE / 'results' / 'leaf_*.json'))), "step-S mismatches with pass 1:", mismatch, "; distinct skeletons seen in pass 1:", len(p1), flush=True)
        outcomes = {}; inconsistent = 0; reused = 0; bug_rerun = 0
        need = {}
        for lf in leaves:
            for sk in lf["skeletons"]:
                need.setdefault(sig_of(sk["roles"], sk["status"]), (sk["roles"], sk["status"]))
        pend_new = []; pend_long = []
        for sg, (roles, status) in need.items():
            recs = p1.get(sg, [])
            done = [x for x in recs if x["status"] == "done"]
            if len({(x["survivors"] > 0) for x in done}) > 1: inconsistent += 1
            has_r0u2 = any(r == 0 and len(L) >= 2 for r, L in roles)
            ok = [x for x in done if x["survivors"] == 0 and (x.get("mode") == "single" or not has_r0u2 or any(c == 0 for c in (x.get("seg_counts") or [])))]
            if ok:
                x = ok[0]; reused += 1
                outcomes[sg] = dict(source="pass1", status="done", survivors=0, nodes=x["geo_stats"].get("nodes", 0) + x["geo_stats"].get("seg_nodes", 0),
                                    mode=x.get("mode"), seg_counts=x.get("seg_counts"), stats=x.get("geo_stats"), deepest=(x.get("deepest_pruned") or [])[:3])
            else:
                if done and all(x["survivors"] == 0 for x in done): bug_rerun += 1
                (pend_long if any(x["status"] == "timeout" for x in recs) else pend_new).append((sg, roles, status))
        print(f"distinct skeletons needed {len(need)}: reused from pass 1 {reused}, to run {len(pend_new) + len(pend_long)} (of them re-run because of the product-phase bug {bug_rerun}, "
              f"timed out in pass 1 {len(pend_long)}); pass-1 inconsistencies {inconsistent}", flush=True)
        # ---- 3. geometry: round A (short cap), round B (long cap) within the budget
        used = 0.0; cache = {}
        def run_round(jobs, cap, label):
            nonlocal used
            n = 0
            for res in pool.imap_unordered(geom, [(sg, roles, status, cap) for sg, roles, status in jobs], chunksize=1):
                cache[res["sig"]] = res; used += res["cpu"]; n += 1
                if n % 50 == 0 or res["status"] != "done" or res["survivors"]:
                    print(f"  [{label} {n}/{len(jobs)}] {res['status']} survivors {res['survivors']} nodes {res['nodes']} cpu {res['cpu']}s segs {res['segments']} roles {res['roles']} {''.join(res['status_slots'])}  (used {used:.0f}s)", flush=True)
        run_round(pend_new, args.capA, "A")
        left = [(sg, roles, status) for sg, roles, status in pend_new if cache[sg]["status"] == "timeout"] + pend_long
        # priority: skeletons that are the only unresolved one of some leaf, then by the number of leaves containing them
        def unresolved_of(lf): return [sig_of(sk["roles"], sk["status"]) for sk in lf["skeletons"] if sig_of(sk["roles"], sk["status"]) not in outcomes and cache.get(sig_of(sk["roles"], sk["status"]), {}).get("status") != "done"]
        solo = Counter(); cnt = Counter()
        for lf in leaves:
            u = unresolved_of(lf)
            if any(cache.get(sig_of(sk["roles"], sk["status"]), {}).get("survivors") for sk in lf["skeletons"]): continue   # leaf already SURVIVING
            for sg in u: cnt[sg] += 1
            if len(u) == 1: solo[u[0]] += 1
        left = [j for j in left if cnt[j[0]] > 0]
        left.sort(key=lambda j: (-solo[j[0]], -cnt[j[0]]))
        budget_left = args.budget - used
        if left and budget_left > 30:
            capB = max(30.0, min(args.capBmax, budget_left / len(left)))
            nB = int(budget_left // capB)
            print(f"round B: {len(left)} skeletons left that matter, budget left {budget_left:.0f}s, cap {capB:.0f}s, running the first {min(nB, len(left))} by priority", flush=True)
            run_round(left[:nB], capB, "B")
        for sg, res in cache.items():
            outcomes[sg] = dict(source="pass2", status=res["status"], survivors=res["survivors"], nodes=res["nodes"], mode=res["mode"], seg_counts=res["seg_counts"],
                                stats=res["stats"], snaps=res["snaps"], cap=res["cap"], deepest=res["deepest"])
        for sg in need:
            if sg not in outcomes: outcomes[sg] = dict(source="none", status="not_run", survivors=0, nodes=0)
        json.dump({sg: {k: v for k, v in o.items() if k != "snaps"} for sg, o in outcomes.items()}, open(OUT / "skeleton_cache.json", "w"))
        print(f"geometry done: cpu {used:.0f}s; outcomes {Counter(o['status'] for o in outcomes.values())}; with survivors {sum(1 for o in outcomes.values() if o['survivors'])}", flush=True)
        # ---- 4. per leaf
        fin = pool.map(finalize, [(lf, {sig_of(sk["roles"], sk["status"]): outcomes[sig_of(sk["roles"], sk["status"])] for sk in lf["skeletons"]}) for lf in leaves], chunksize=1)
    summ = dict(leaves=len(fin), results=dict(Counter(f["result"] for f in fin)), excluded_by=dict(Counter(f.get("excluded_by") for f in fin if f["result"] == "EXCLUDED")),
                step_S_cpu=round(cpu_s), geometry_cpu=round(used), finalize_cpu=round(sum(f["finalize_cpu"] for f in fin)), wall=round(time.time() - t0),
                distinct_skeletons=len(need), reused_from_pass1=reused, rerun_for_bug=bug_rerun, pass1_inconsistencies=inconsistent, stepS_mismatches=mismatch,
                pass2_outcomes=dict(Counter(o["status"] for o in outcomes.values() if o["source"] == "pass2")), leaves_list=fin)
    json.dump(summ, open(OUT / "summary.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in summ.items() if k != "leaves_list"}, indent=1))


if __name__ == "__main__":
    main()
