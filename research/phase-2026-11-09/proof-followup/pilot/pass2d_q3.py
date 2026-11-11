#!/usr/bin/env python3
"""pass2d_q3.py -- round D of the second pass: multi-segment skeletons whose plain product of segment realizations was capped.

run_join does what enum_q3.run_skeleton does for several segments, with one necessary condition applied BEFORE the product:
a deferred helper with r = 0 and u >= 2 whose slots are concrete needs one mask h with h + l_s in B for every slot s it
carries and h not in B ((D-b), (D-2), R1 of PILOT_SPEC.md).  The segment realizations are indexed by their label values;
label combinations admitting no such mask for some deferred helper are skipped (no placement of that helper can exist for
them); the surviving combinations go through exactly the product-phase code of run_skeleton (R1 across segments, R7 on the
union through Realizer(init=...), placement of the deferred helpers).  Exhausting the combinations is an exclusion, a
deadline or a cap is not.

Validation before use (both must pass, else nothing is applied):
  V1  on multi-segment skeletons with deferred helpers that the plain product DECIDED in pass 2 (status done), the join must
      give the same verdict (realizable or not);
  V2  guided search on P5 objects (real phases) whose skeleton has several segments and a deferred r = 0, u >= 2 helper:
      the join must reach the object.
Then: every skeleton of results_final/ that is multi-segment, has deferred helpers and is not done is run with the join
(CPU cap per skeleton), and the leaf files are updated (previous versions kept in results_final/before_roundD/).
usage: python3 pass2d_q3.py [--cap 120] [--budget 1500] [--workers 6]
"""
import sys, json, glob, time, shutil, itertools, argparse, random
from collections import Counter, defaultdict
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import enum_q3 as E, verify_q3 as V, pass2_q3 as P2
RD = HERE / "results_final"


def run_join(geo, pl, deadline, guide=None, seg_cap=150_000, max_store=6, max_combos=5_000_000):
    segs = pl["segments"]; roles = pl["roles"]; st = Counter()
    n_seg_entries = sum(len(s["order"]) for s in segs); rider_entries = list(pl["order"][n_seg_entries:])
    def bad(R): return bool(R.stats.get("no_concrete_role") or R.stats.get("rider_no_concrete_slot"))
    seg_real = []; seg_counts = []
    for seg in segs:
        R = E.Realizer(geo, pl, seg["order"], max_store=seg_cap, max_survivors=seg_cap, deadline=deadline, guide=guide); R.run()
        for k2, v in R.stats.items(): st["seg_" + k2] += v
        if bad(R): return dict(status="error", survivors=0, snaps=[], stats=dict(st), seg_counts=seg_counts)
        if R.timed_out: return dict(status="timeout", survivors=0, snaps=[], stats=dict(st), seg_counts=seg_counts)
        seg_counts.append(R.stats["survivors"])
        if R.stats["survivors"] == 0: return dict(status="done", survivors=0, snaps=[], stats=dict(st), seg_counts=seg_counts)
        if R.stats["survivors"] >= seg_cap: return dict(status="capped", survivors=0, snaps=[], stats=dict(st), seg_counts=seg_counts)
        slots = sorted(seg["slots"]); idx = defaultdict(list)
        for snap in R.survivors: idx[tuple(snap["labels"][s] for s in slots)].append(snap)
        seg_real.append((slots, idx))
    rider_slots = [roles[e[0]][1] for e in rider_entries]
    B = geo.B; Bset = geo.Bset; PM = geo.PM
    def compatible(lab):
        for L in rider_slots:
            known = [s for s in L if lab[s] is not None]
            if len(known) < 2: continue
            l0 = lab[known[0]]
            if any((l0 ^ lab[s]) not in PM for s in known[1:]): return False
            if not any((l0 ^ b) not in Bset and all(((l0 ^ b) ^ lab[s]) in Bset for s in known[1:]) for b in B): return False
        return True
    order = sorted(range(len(seg_real)), key=lambda j: len(seg_real[j][1]))
    found = []; status = ["done"]; n_combo = [0]
    def process(chosen):
        for combo in itertools.product(*chosen):
            n_combo[0] += 1
            if n_combo[0] > max_combos: status[0] = "capped"; return True
            if deadline is not None and (n_combo[0] & 255) == 0 and time.process_time() > deadline: status[0] = "timeout"; return True
            labels = [None] * 3; helpers = []; masks = set(); ok = True
            for snap in combo:
                for s in range(3):
                    if snap["labels"][s] is not None: labels[s] = snap["labels"][s]
                for h, R_, ends, i in snap["helpers"]:
                    if h in masks: ok = False
                    masks.add(h); helpers.append((h, R_, ends, i))
            if not ok: st["combo_R1"] += 1; continue
            R = E.Realizer(geo, pl, rider_entries, max_store=max_store, max_survivors=1, deadline=deadline, init=dict(labels=labels, helpers=helpers), guide=guide)
            if not R.init_ok: st["combo_R7"] += 1; continue
            R.run()
            for k2, v in R.stats.items(): st["prod_" + k2] += v
            if bad(R): status[0] = "error"; return True
            if R.timed_out: status[0] = "timeout"; return True
            if R.stats["survivors"]: found.extend(R.survivors); return True
        return False
    def rec(j, lab, chosen):
        if j == len(order): return process(chosen)
        slots, idx = seg_real[order[j]]
        for tup, snaps in idx.items():
            if deadline is not None and time.process_time() > deadline: status[0] = "timeout"; return True
            used = {l for l in lab if l is not None}
            if any(l in used for l in tup): st["join_label_clash"] += 1; continue
            for s, l in zip(slots, tup): lab[s] = l
            if compatible(lab):
                st["join_compatible"] += 1
                if rec(j + 1, lab, chosen + [snaps]):
                    for s in slots: lab[s] = None
                    return True
            else: st["join_incompatible"] += 1
            for s in slots: lab[s] = None
        return False
    rec(0, [None] * 3, [])
    st["combinations_tried"] = n_combo[0]
    return dict(status=status[0], survivors=len(found), snaps=found, stats=dict(st), seg_counts=seg_counts)


def job(task):
    sg, roles, status, cap = task; c0 = time.process_time()
    geo = E.build_geo()
    skel = dict(roles=roles, status=status, W=[sum(r for r, L in roles if s in L) for s in range(3)])
    pl = E.plan(skel, sym_first_root=True)
    try: res = run_join(geo, pl, time.process_time() + cap)
    except MemoryError: res = dict(status="capped", survivors=0, snaps=[], stats={}, seg_counts=[])
    res.update(sig=sg, roles=roles, status_slots=status, cap=cap, cpu=round(time.process_time() - c0, 2), mode="join",
               nodes=res["stats"].get("seg_nodes", 0) + res["stats"].get("prod_nodes", 0))
    return res


def plain(task):
    sg, roles, status, cap = task
    geo = E.build_geo()
    skel = dict(roles=roles, status=status, W=[sum(r for r, L in roles if s in L) for s in range(3)])
    pl = E.plan(skel, sym_first_root=True)
    return sg, job(task)


def is_target(roles, status):
    skel = dict(roles=roles, status=status, W=[sum(r for r, L in roles if s in L) for s in range(3)])
    pl = E.plan(skel, sym_first_root=True)
    return len(pl["segments"]) >= 2 and len(pl["riders2"]) >= 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--cap", type=float, default=120.0); ap.add_argument("--budget", type=float, default=1500.0); ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    t0 = time.time(); geo = E.build_geo(); rng = random.Random(3)
    cache = json.load(open(RD / "skeleton_cache.json"))
    import multiprocessing as mp
    out = {}
    with mp.get_context("fork").Pool(args.workers) as pool:
        # ---- V1: same verdict as the plain product where the plain product decided
        decided = []
        for sg, o in cache.items():
            roles, status = json.loads(sg); status = list(status)
            if o["source"] == "pass2" and o["status"] == "done" and o.get("mode") == "segments" and is_target(roles, status): decided.append((sg, roles, status, o))
        rng.shuffle(decided); sample = decided[:36]
        v1 = []; cpu = 0.0
        for res in pool.imap_unordered(job, [(sg, roles, status, 20.0) for sg, roles, status, o in sample], chunksize=1):
            o = cache[res["sig"]]; cpu += res["cpu"]
            v1.append(dict(sig=res["sig"], plain=o["survivors"] > 0, join_status=res["status"], join=res["survivors"] > 0, agree=(res["status"] != "done" or (res["survivors"] > 0) == (o["survivors"] > 0))))
        out["V1"] = dict(decided_available=len(decided), tested=len(v1), join_done=sum(1 for x in v1 if x["join_status"] == "done"), disagreements=sum(1 for x in v1 if not x["agree"]),
                         both_realizable=sum(1 for x in v1 if x["join_status"] == "done" and x["join"] and x["plain"]), both_empty=sum(1 for x in v1 if x["join_status"] == "done" and not x["join"] and not x["plain"]), cpu=round(cpu))
        print("V1:", out["V1"], flush=True)
        # ---- V2: guided P5 objects with several segments and deferred helpers
        import controls_p5 as P5
        geos = {"Mt": geo, "M": P5.make_geo("M")}
        by_shape, n_sub, n_d2 = P5.real_objects(geos, 3)
        n2 = 0; miss2 = 0; c0 = time.process_time()
        for (ori, _, _), lst in by_shape.items():
            for _, obj in lst:
                skel, slot_of = P5.skeleton_of(obj)
                pl = E.plan(skel, sym_first_root=True)
                if not (len(pl["segments"]) >= 2 and pl["riders2"]): continue
                croles = {pl["roles"][e[0]] for e in pl["order"]}
                labels = [None] * 3
                for j, s in slot_of.items(): labels[s] = obj["labels"][j]["value"]
                helpers = [((hp["r"], tuple(sorted(slot_of[j] for j in hp["labels"]))), hp["mask"], frozenset(hp["triples"])) for hp in obj["helpers"]]
                th = [h for h in helpers if h[0] in croles]; tl = labels; found = False
                cslots = sorted({s for role, _, _ in th for s in role[1]})
                for _rot in range(4):
                    res = run_join(geos[ori], pl, None, guide=P5.Guide(tl, th))
                    for snap in res["snaps"]:
                        got = {(pl["roles"][i], h, frozenset(R)) for h, R, ends, i in snap["helpers"]}
                        if got == set(th) and all(snap["labels"][s] == tl[s] for s in cslots if snap["labels"][s] is not None): found = True
                    if found: break
                    tl, th = P5.rotate(geos[ori], tl, th)
                n2 += 1; miss2 += (not found)
        out["V2"] = dict(objects=n2, misses=miss2, cpu=round(time.process_time() - c0))
        print("V2:", out["V2"], flush=True)
        ok = out["V1"]["disagreements"] == 0 and out["V1"]["join_done"] >= 20 and out["V2"]["misses"] == 0 and out["V2"]["objects"] >= 100
        out["validated"] = ok
        if not ok:
            json.dump(out, open(RD / "roundD_outcome.json", "w"), indent=1); print("VALIDATION FAILED: nothing applied"); sys.exit(2)
        # ---- targets: not-done multi-segment skeletons with deferred helpers that still matter
        need = defaultdict(list)
        for fn in sorted(glob.glob(str(RD / "leaf_*.json"))):
            r = json.load(open(fn))
            if r["result"] != "UNRESOLVED": continue
            st = E.slot_status(r["A"], r["qD"])
            for sk in r["skeleton_list"]:
                if sk["status"] != "done" and is_target(sk["roles"], st): need[P2.sig_of(sk["roles"], st)].append(fn)
        jobs = sorted(need, key=lambda sg: -len(need[sg]))
        nmax = int(args.budget // args.cap)
        print(f"round D targets: {len(jobs)} distinct skeletons in UNRESOLVED leaves; running {min(nmax, len(jobs))} with cap {args.cap}s", flush=True)
        results = {}; used = 0.0
        for res in pool.imap_unordered(job, [(sg, json.loads(sg)[0], list(json.loads(sg)[1]), args.cap) for sg in jobs[:nmax]], chunksize=1):
            results[res["sig"]] = res; used += res["cpu"]
            print(f"  {res['status']} survivors {res['survivors']} seg_counts {res['seg_counts']} combos {res['stats'].get('combinations_tried')} compatible {res['stats'].get('join_compatible')} cpu {res['cpu']}s {res['roles']} {''.join(res['status_slots'])}", flush=True)
    out["roundD"] = dict(targets=len(jobs), run=len(results), outcomes=dict(Counter(r["status"] for r in results.values())), with_survivors=sum(1 for r in results.values() if r["survivors"]), cpu=round(used))
    # ---- update the leaf files
    bak = RD / "before_roundD"; bak.mkdir(exist_ok=True); changed = []
    for fn in sorted(glob.glob(str(RD / "leaf_*.json"))):
        r = json.load(open(fn)); st = E.slot_status(r["A"], r["qD"]); key = tuple(r["key"]); a = r["A"]; d = r["qD"]; touched = False
        for sk in r["skeleton_list"]:
            res = results.get(P2.sig_of(sk["roles"], st))
            if res is None or sk["status"] == "done" or res["status"] != "done": continue
            if not touched: shutil.copy(fn, bak / Path(fn).name); touched = True
            sk.update(source="pass2-roundD(join)", status="done", survivors=res["survivors"], nodes=res["nodes"], mode="join", seg_counts=res["seg_counts"], geo_stats=res["stats"], cap=res["cap"])
            if res["survivors"]:
                pl = E.plan(dict(roles=sk["roles"], status=st, W=sk["W"]), sym_first_root=True); ok_w = 0
                for snap in res["snaps"][:5]:
                    obj, rep = E.complete_witness(geo, pl, snap, key, a, d)
                    w = dict(skeleton=sk["roles"], object=obj, verify={k: [v[0], v[1]] for k, v in rep.items() if isinstance(v, tuple)})
                    if rep["all"][0]: w["milp"] = V.milp_status(key, a, d, dict(V.counts_of(obj))); ok_w += 1
                    r["witnesses"].append(w)
                sk["witnesses_verified"] = ok_w
                if ok_w: r["survivors"] += res["survivors"]
            r["unresolved_skeletons"] = [u for u in r["unresolved_skeletons"] if u["roles"] != sk["roles"]]
            if res["survivors"] and not sk.get("witnesses_verified"): r["unresolved_skeletons"].append(dict(roles=sk["roles"], status="witness completion failed"))
        if touched:
            r["nodes"] = sum(e["nodes"] for e in r["skeleton_list"])
            r["result"] = "SURVIVING" if r["survivors"] else ("UNRESOLVED" if r["unresolved_skeletons"] else "EXCLUDED")
            if r["result"] == "EXCLUDED": r["excluded_by"] = "step G (geometry)"
            r["witness_verify_all"] = all(w["verify"]["all"][0] for w in r["witnesses"]) if r["witnesses"] else None
            json.dump(r, open(fn, "w")); changed.append([list(key), a, d, r["result"]])
    out["changed_leaves"] = changed; out["seconds"] = round(time.time() - t0)
    json.dump(dict(out, results={sg: {k: v for k, v in r.items() if k != "snaps"} for sg, r in results.items()}), open(RD / "roundD_outcome.json", "w"), indent=1)
    print(json.dumps(out, indent=1))
