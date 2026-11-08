#!/usr/bin/env python3
"""exp1 analysis: the pre-registered items of translog/REPORT.md.

Usage: analyze_exp1.py [exact_cap_seconds=1800] [max_hops=400]
Reads exp1/runs/E1/workers/*/translog.jsonl, status.json, exp1/samples/samples.jsonl,
exp1/sigcache.json (v3 signatures; missing ones are computed), exp1/seeds.json.
Writes exp1/analysis.json and exp1/exact.jsonl (one line per exact cataloguing item).

Items:
 Q1 per-worker entry/excursion/stay statistics (translog/analyze.py's analyse_log);
 Q2 plateau identity: v3 signatures per entry (visits, hops, revisits) and EXACT identity via
    pes_lib.compress for (b) every cross-worker v3 coincidence and (a) a random sample of
    consecutive hops with excursion < 2 s (exit 89 state -> next entry state), under a time cap;
 Q3 connectivity: P and M against the R2 null model (N_eff = 1.3e5), all / cross / same-start
    pairs, and the same-start pairs' separation and re-meeting;
 Q4 sampler calibration: the 30 s sampler's view of the same hour next to the log's truth.
"""
import glob
import json
import os
import random
import signal
import statistics as st
import sys
import time
from collections import Counter, defaultdict

sys.path.insert(0, os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/translog"))
sys.path.insert(0, "/home/joebachir20/xs-campaigns/2026-11-05-exit/pes")
import analyze as A  # noqa: E402  (translog/analyze.py: analyse_log, pair_sampler)
import plateau_sig as ps  # noqa: E402
import pes_lib  # noqa: E402

E = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/translog/exp1")
RUNS = os.path.join(E, "runs/E1/workers")
SAMPLES = os.path.join(E, "samples/samples.jsonl")
EXACT_CAP = float(sys.argv[1]) if len(sys.argv) > 1 else 1800.0
MAX_HOPS = int(sys.argv[2]) if len(sys.argv) > 2 else 400
PER_CALL = float(sys.argv[3]) if len(sys.argv) > 3 else 60.0


class CompressTimeout(Exception):
    pass


def _alarm(signum, frame):
    raise CompressTimeout()


signal.signal(signal.SIGALRM, _alarm)
N_EFF = 1.3e5
sp = ps.sp


def q(xs, p):
    xs = sorted(xs)
    return xs[max(0, min(len(xs) - 1, int(round(p * (len(xs) - 1)))))] if xs else None


# ------------------------------------------------------------------ load
workers = sorted(os.path.basename(w) for w in glob.glob(RUNS + "/*"))
group = {w: w.split("-")[0] for w in workers}
logs, status, rows_by = {}, {}, {}
for w in workers:
    status[w] = json.load(open(f"{RUNS}/{w}/status.json"))
    meta, body = A.load_rows(f"{RUNS}/{w}/translog.jsonl")
    body.sort(key=lambda r: r["it"])
    rows_by[w] = (meta, body)
sigcache = json.load(open(os.path.join(E, "sigcache.json"))) if os.path.exists(os.path.join(E, "sigcache.json")) else {}


def sig_of_row(r):
    i = r["id"]
    if i not in sigcache:
        s, info = ps.sig_of(r["v"])
        sigcache[i] = [s, info[0], info[1], info[2]] if s else [None, info, 0, 0]
    return sigcache[i][0]


# ------------------------------------------------------------------ Q1
Q1 = {}
pooled = defaultdict(list)
for w in workers:
    meta, body = rows_by[w]
    res, segs, e88 = A.analyse_log(f"{RUNS}/{w}/translog.jsonl", status[w]["t"])
    res["sampler"] = A.pair_sampler(__import__("pathlib").Path(SAMPLES), "E1", w, segs, e88)
    res["steps"] = status[w]["steps"]
    res["steps_per_s"] = round(status[w]["steps"] / status[w]["t"], 1)
    res["translog_rows"] = len(body)
    res.pop("below_88_segments_detail", None)
    res["below_88"] = len(res.pop("below_88_segments"))
    Q1[w] = res
    for k in ("entries_88_per_min", "distinct_88_ids", "entries_88", "excursions_shorter_than_30s",
              "excursions_shorter_than_2s", "steps_per_s", "recurring_ids"):
        pooled[k].append(res[k])
    pooled["exc_med_s"].append(res["excursion_seconds"]["median"])
    pooled["exc_med_steps"].append(res["excursion_steps"]["median"])
    pooled["stay_med_s"].append(res["stay_88_seconds"]["median"])
    pooled["share88"].append(res["time_share_by_gates"].get("88", 0))
    pooled["share89"].append(res["time_share_by_gates"].get("89", 0))
Q1_pooled = {k: {"min": min(v), "median": st.median(v), "max": max(v), "sum": sum(v)} for k, v in pooled.items()}

# ------------------------------------------------------------------ Q2 v3 level
entries = {}            # worker -> list of entry dicts (88 segments with values) in order
for w in workers:
    meta, body = rows_by[w]
    close = meta["close"]
    t_end = close["t"] if close else status[w]["t"]
    lst = []
    for i, r in enumerate(body):
        if r["g"] != 88 or not r.get("v"):
            continue
        nxt = body[i + 1] if i + 1 < len(body) else None
        lst.append({"w": w, "i": len(lst), "it0": r["it"], "t0": r["t"], "it1": nxt["it"] if nxt else None,
                    "t1": nxt["t"] if nxt else t_end, "v": r["v"], "id": r["id"], "k": r["k"],
                    "exit_row": nxt, "sig": sig_of_row(r)})
    entries[w] = lst
json.dump(sigcache, open(os.path.join(E, "sigcache.json"), "w"))

Q2 = {"per_worker": {}}
visits_by, nodes_by, runs_by = {}, {}, {}
for w in workers:
    lst = entries[w]
    sigs = [e["sig"] for e in lst]
    runs = []
    cur, start = None, None
    for i, s in enumerate(sigs):
        if s != cur:
            if cur is not None:
                runs.append((cur, start, i - 1))
            cur, start = s, i
    if cur is not None:
        runs.append((cur, start, len(sigs) - 1))
    runs_by[w] = runs
    visits_by[w] = len(runs)
    nodes_by[w] = set(sigs)
    order = [r[0] for r in runs]
    first, revisit = {}, 0
    for i, s in enumerate(order):
        if s in first:
            revisit += 1
        first[s] = first.get(s, i)
    hops_s = []
    for a, b in zip(runs, runs[1:]):
        hops_s.append(lst[b[1]]["t0"] - lst[a[2]]["t1"])
    span = lst[-1]["t1"] - lst[0]["t0"] if lst else 1
    Q2["per_worker"][w] = {
        "entries": len(lst), "distinct_v3": len(nodes_by[w]), "visits": len(runs),
        "visits_per_h": round(len(runs) / span * 3600, 1), "distinct_v3_per_h": round(len(nodes_by[w]) / span * 3600, 1),
        "hops": len(hops_s), "hop_excursion_s_median": q(hops_s, .5), "hop_excursion_lt30s": round(sum(1 for x in hops_s if x < 30) / len(hops_s), 4) if hops_s else None,
        "revisits": revisit, "v3_visited_more_than_once": sum(1 for n in Counter(order).values() if n > 1),
        "entries_per_visit_median": q([b - a + 1 for _, a, b in runs], .5),
        "downs_in_fans": sum(1 for e in lst if sigcache.get(e["id"], [None, None, 0, 0])[3])}
Q2["pooled"] = {"entries": sum(len(entries[w]) for w in workers),
                "distinct_v3_all_workers": len(set().union(*nodes_by.values())),
                "visits_all": sum(visits_by.values()),
                "visits_per_worker_h_median": st.median(Q2["per_worker"][w]["visits_per_h"] for w in workers),
                "distinct_v3_per_worker_h_median": st.median(Q2["per_worker"][w]["distinct_v3_per_h"] for w in workers),
                "states_with_down_exit_in_fan": sum(Q2["per_worker"][w]["downs_in_fans"] for w in workers)}

# ------------------------------------------------------------------ Q3 connectivity (v3)
seed_sig = {}
for w in workers:
    seed_sig[w] = entries[w][0]["sig"] if entries[w] else None
pairs = [(a, b) for i, a in enumerate(workers) for b in workers[i + 1:]]
same = [(a, b) for a, b in pairs if group[a] == group[b]]
cross = [(a, b) for a, b in pairs if group[a] != group[b]]


def shared_nodes(a, b, drop_seed=False):
    s = nodes_by[a] & nodes_by[b]
    if drop_seed:
        s = s - {seed_sig[a]}
    return s


def pm(pair_list, drop_seed=False):
    P = sum(len(nodes_by[a]) * len(nodes_by[b]) for a, b in pair_list)
    Pv = sum(visits_by[a] * visits_by[b] for a, b in pair_list)
    incid = sum(len(shared_nodes(a, b, drop_seed)) for a, b in pair_list)
    nodes = set()
    for a, b in pair_list:
        nodes |= shared_nodes(a, b, drop_seed)
    exp = P / N_EFF
    lo, hi = exp - 1.96 * exp ** 0.5, exp + 1.96 * exp ** 0.5
    return {"pairs": len(pair_list), "P_nodes": P, "P_visits": Pv, "M_nodes": len(nodes),
            "M_pair_incidences": incid, "expected_P_over_Neff": round(exp, 2),
            "poisson95": [round(max(0, lo), 1), round(hi, 1)],
            "verdict": ("inside: one pool sparsely wandered" if lo <= incid <= hi else
                        ("above: hubs / small region" if incid > hi else "below: local trails"))}


Q3 = {"N_eff": N_EFF, "all_pairs": pm(pairs), "cross_pairs": pm(cross),
      "same_start_pairs": pm(same, drop_seed=True), "same_start_detail": []}
for a, b in same:
    la, lb = entries[a], entries[b]
    s0 = seed_sig[a]
    # separation: the first time each has left the start signature for good (last entry on s0)
    last_a = max((e["t0"] for e in la if e["sig"] == s0), default=None)
    last_b = max((e["t0"] for e in lb if e["sig"] == s0), default=None)
    first_leave_a = next((e["t0"] for e in la if e["sig"] != s0), None)
    first_leave_b = next((e["t0"] for e in lb if e["sig"] != s0), None)
    sh = shared_nodes(a, b, drop_seed=True)
    # re-meetings: shared signatures first entered by both after each had left s0 once
    remeet = []
    for s in sh:
        ta = next(e["t0"] for e in la if e["sig"] == s)
        tb = next(e["t0"] for e in lb if e["sig"] == s)
        if first_leave_a is not None and first_leave_b is not None and ta > first_leave_a and tb > first_leave_b:
            remeet.append({"sig": s, "t_a": round(ta), "t_b": round(tb),
                           "entries_a": sum(1 for e in la if e["sig"] == s), "entries_b": sum(1 for e in lb if e["sig"] == s)})
    Q3["same_start_detail"].append({
        "pair": [a, b], "start_sig": s0, "nodes": [len(nodes_by[a]), len(nodes_by[b])],
        "first_leave_start_s": [first_leave_a, first_leave_b], "last_on_start_s": [last_a, last_b],
        "entries_on_start_sig": [sum(1 for e in la if e["sig"] == s0), sum(1 for e in lb if e["sig"] == s0)],
        "shared_excluding_start": len(sh), "expected_null": round(len(nodes_by[a]) * len(nodes_by[b]) / N_EFF, 3),
        "re_meetings_after_both_left_start": len(remeet), "re_meeting_examples": sorted(remeet, key=lambda r: r["t_a"])[:5]})
Q3["cross_pair_detail"] = sorted([{"pair": [a, b], "shared": len(shared_nodes(a, b)),
                                   "expected_null": round(len(nodes_by[a]) * len(nodes_by[b]) / N_EFF, 3)}
                                  for a, b in cross], key=lambda d: -d["shared"])[:15]
coinc = defaultdict(set)
for w in workers:
    for s in nodes_by[w]:
        coinc[s].add(w)
multi = {s: ws for s, ws in coinc.items() if len(ws) > 1}
Q3["v3_nodes_with_2plus_workers"] = len(multi)
Q3["v3_nodes_with_2plus_groups"] = sum(1 for ws in multi.values() if len({group[w] for w in ws}) > 1)

# ------------------------------------------------------------------ Q4 sampler calibration
Q4 = {"per_worker": {}}
recs = [json.loads(l) for l in open(SAMPLES)] if os.path.exists(SAMPLES) else []
snodes = {}
for w in workers:
    mine = [r for r in recs if r["worker"] == w]
    for k, r in enumerate(mine):
        r["idx"] = k
    s88 = [r for r in mine if r["gates"] == 88]
    span_h = (mine[-1]["wall"] - mine[0]["wall"]) / 3600 if len(mine) > 1 else None
    hops = 0
    hops_no89 = 0
    for a, b in zip(mine, mine[1:]):
        pass
    # F11 hop: consecutive 88 samples with different hashes; "no 89 sample" when adjacent in the record list
    last88 = None
    for r in mine:
        if r["gates"] == 88:
            if last88 is not None and r["hash"] != last88["hash"]:
                hops += 1
                if r["idx"] - last88["idx"] == 1:
                    hops_no89 += 1
            last88 = r
    ss = []
    for r in s88:
        if r["hash"] not in sigcache:
            sg, info = ps.sig_of(r["values"])
            sigcache[r["hash"]] = [sg, info[0], info[1], info[2]] if sg else [None, info, 0, 0]
        ss.append(sigcache[r["hash"]][0])
    snodes[w] = set(ss)
    Q4["per_worker"][w] = {"records": len(mine), "samples_88": len(s88), "samples_89": sum(1 for r in mine if r["gates"] == 89),
                           "hops_sampler": hops, "hops_sampler_per_h": round(hops / span_h, 1) if span_h else None,
                           "hops_without_89_sample": hops_no89,
                           "distinct_v3_sampled": len(snodes[w]), "distinct_v3_log": len(nodes_by[w]),
                           "entries_log": len(entries[w]), "visits_log": visits_by[w]}
# index records for adjacency
for w in workers:
    pass
json.dump(sigcache, open(os.path.join(E, "sigcache.json"), "w"))
Ps = sum(len(snodes[a]) * len(snodes[b]) for a, b in pairs)
Ms = set()
Mi = 0
for a, b in pairs:
    sh = snodes[a] & snodes[b]
    Ms |= sh
    Mi += len(sh)
Q4["sampler_P_nodes"] = Ps
Q4["sampler_M_nodes"] = len(Ms)
Q4["sampler_M_pair_incidences"] = Mi
Q4["sampler_expected_null"] = round(Ps / N_EFF, 3)
Q4["pooled"] = {"hops_sampler": sum(v["hops_sampler"] for v in Q4["per_worker"].values()),
                "hops_without_89_sample": sum(v["hops_without_89_sample"] for v in Q4["per_worker"].values()),
                "samples_88": sum(v["samples_88"] for v in Q4["per_worker"].values()),
                "distinct_v3_sampled_all": len(set().union(*snodes.values())) if snodes else 0,
                "entries_log": sum(len(entries[w]) for w in workers),
                "visits_log": sum(visits_by.values())}

# ------------------------------------------------------------------ Q2 exact cataloguing
exact_log = open(os.path.join(E, "exact.jsonl"), "w")
t_exact0 = time.time()


def hk_of(values):
    helpers = [v for v in values if v not in sp.tset]
    stt = sp.state(helpers)
    if stt.count() != 88 or stt.depth() is None:
        return None
    return sp.hkey(stt)


PL_CACHE = {}   # v3 signature -> list of (Plateau, info) already computed


def compress_state(values, time_limit=None, sig=None):
    hk = hk_of(values)
    if hk is None:
        return None, {"error": "not an 88 state"}
    if sig is not None:
        for pl0, info0 in PL_CACHE.get(sig, ()):
            if member(pl0, values):
                return pl0, {**info0, "cached": True}
    time_limit = time_limit or PER_CALL
    signal.alarm(int(time_limit) + 5)
    try:
        pl, info = pes_lib.compress(sp, hk, verify_limit=20000, closure_limit=3000, time_limit=time_limit)
    except CompressTimeout:
        return None, {"error": "timeout", "seconds": time_limit}
    finally:
        signal.alarm(0)
    inexact = info.get("verified") == "closure-truncated" or (pl.kind != "product" and info.get("note"))
    out = {"kind": pl.kind, "size": pl.size(), "radices": pl.radices() if pl.kind == "product" else None,
           "verified": info.get("verified"), "note": info.get("note"), "seconds": info.get("seconds"),
           "inexact": bool(inexact), "downs": len(info.get("downs") or [])}
    if sig is not None:
        PL_CACHE.setdefault(sig, []).append((pl, out))
    return pl, out


def member(pl, values):
    hk = hk_of(values)
    if hk is None:
        return None
    for s in sp.shifts:
        rk = sp.rot(hk, s) if s else hk
        if pl.contains(frozenset(rk)):
            return True
    return False


def exact_time_left():
    return EXACT_CAP - (time.time() - t_exact0)


# (b) cross-worker v3 coincidences, most-shared first; cap: 60 % of the exact budget
coinc_items = sorted(multi.items(), key=lambda kv: (-len(kv[1]), kv[0]))
Q2b = {"coincidences_total": len(coinc_items), "tested": 0, "exact_same": 0, "exact_different": 0,
       "inexact": 0, "errors": 0, "by_type": Counter(), "examples": []}
for s, ws in coinc_items:
    if exact_time_left() < 0.6 * EXACT_CAP:
        break
    ws = sorted(ws)
    e0 = next(e for e in entries[ws[0]] if e["sig"] == s)
    try:
        pl, info = compress_state(e0["v"], sig=s)
    except Exception as exc:  # noqa: BLE001
        Q2b["errors"] += 1
        exact_log.write(json.dumps({"item": "coincidence", "sig": s, "error": str(exc)}) + "\n")
        continue
    if pl is None:
        Q2b["timeouts"] = Q2b.get("timeouts", 0) + (info.get("error") == "timeout")
        Q2b["errors"] += info.get("error") != "timeout"
        exact_log.write(json.dumps({"item": "coincidence", "sig": s, "workers": ws, "outcome": info.get("error")}) + "\n")
        continue
    res = {}
    for w in ws[1:]:
        e1 = next(e for e in entries[w] if e["sig"] == s)
        res[w] = member(pl, e1["v"])
    typ = "cross" if len({group[w] for w in ws}) > 1 else "same-start"
    Q2b["tested"] += 1
    if info["inexact"]:
        Q2b["inexact"] += 1
        outcome = "inexact"
    elif all(res.values()):
        Q2b["exact_same"] += 1
        outcome = "same"
    else:
        Q2b["exact_different"] += 1
        outcome = "different"
    Q2b["by_type"][f"{typ}:{outcome}"] += 1
    rec = {"item": "coincidence", "sig": s, "workers": ws, "type": typ, "outcome": outcome, "members": res, **info}
    exact_log.write(json.dumps(rec) + "\n")
    exact_log.flush()
    if len(Q2b["examples"]) < 12:
        Q2b["examples"].append(rec)
Q2b["by_type"] = dict(Q2b["by_type"])
Q2b["seconds"] = round(time.time() - t_exact0, 1)

# (a) consecutive hops with excursion < 2 s: exit 89 state -> next entry; previous entry too
cands = []
for w in workers:
    lst = entries[w]
    for e1, e2 in zip(lst, lst[1:]):
        xr = e1["exit_row"]
        if xr is None or e1["t1"] is None:
            continue
        exc_s = e2["t0"] - e1["t1"]
        if exc_s < 2.0 and xr["g"] == 89 and xr.get("v"):
            cands.append((w, e1, e2, xr, exc_s))
random.Random(1).shuffle(cands)
Q2a = {"candidates": len(cands), "tested": 0, "same": 0, "different": 0, "ambiguous": 0, "inexact": 0,
       "errors": 0, "prev_entry_same": 0, "prev_entry_different": 0, "same_v3": 0, "by_v3_and_exact": Counter(),
       "candidate_counts": [], "examples": []}
t_a0 = time.time()
for w, e1, e2, xr, exc_s in cands[:MAX_HOPS]:
    if exact_time_left() < 0:
        break
    try:
        pl, info = compress_state(e2["v"], sig=e2["sig"])
    except Exception as exc:  # noqa: BLE001
        Q2a["errors"] += 1
        continue
    if pl is None:
        Q2a["timeouts"] = Q2a.get("timeouts", 0) + (info.get("error") == "timeout")
        Q2a["errors"] += info.get("error") != "timeout"
        exact_log.write(json.dumps({"item": "hop", "worker": w, "it_exit": xr["it"], "outcome": info.get("error"),
                                    "v3_same": e1["sig"] == e2["sig"]}) + "\n")
        continue
    X = xr["v"]
    helpers = [v for v in X if v not in sp.tset]
    cand_states = []
    for u in helpers:
        vals = [v for v in X if v != u]
        if hk_of(vals) is not None:
            cand_states.append(vals)
    mem = [member(pl, c) for c in cand_states]
    prev = member(pl, e1["v"])
    Q2a["tested"] += 1
    Q2a["candidate_counts"].append(len(cand_states))
    if info["inexact"]:
        Q2a["inexact"] += 1
        outcome = "inexact"
    elif mem and all(mem):
        Q2a["same"] += 1
        outcome = "same"
    elif mem and not any(mem):
        Q2a["different"] += 1
        outcome = "different"
    else:
        Q2a["ambiguous"] += 1
        outcome = "ambiguous"
    if prev:
        Q2a["prev_entry_same"] += 1
    elif prev is False:
        Q2a["prev_entry_different"] += 1
    v3same = e1["sig"] == e2["sig"]
    Q2a["same_v3"] += v3same
    Q2a["by_v3_and_exact"][f"v3 {'same' if v3same else 'diff'} / exact {outcome}"] += 1
    rec = {"item": "hop", "worker": w, "it_exit": xr["it"], "exc_s": round(exc_s, 3), "exit_move": xr["m"],
           "entry_move": None, "n_candidates": len(cand_states), "members": mem, "prev_entry_member": prev,
           "v3_same": v3same, "outcome": outcome, **info}
    exact_log.write(json.dumps(rec) + "\n")
    exact_log.flush()
    if len(Q2a["examples"]) < 12:
        Q2a["examples"].append(rec)
Q2a["by_v3_and_exact"] = dict(Q2a["by_v3_and_exact"])
Q2a["candidate_counts"] = {"median": q(Q2a["candidate_counts"], .5), "max": max(Q2a["candidate_counts"], default=None)}
Q2a["seconds"] = round(time.time() - t_a0, 1)
exact_log.close()
Q2["exact_coincidences"] = Q2b
Q2["exact_hops"] = Q2a
Q2["exact_total_seconds"] = round(time.time() - t_exact0, 1)

out = {"workers": workers, "groups": group, "Q1": Q1, "Q1_pooled": Q1_pooled, "Q2": Q2, "Q3": Q3, "Q4": Q4,
       "status": {w: {"steps": status[w]["steps"], "t": status[w]["t"], "phase": status[w]["phase"],
                      "best": status[w]["best"] and status[w]["best"]["gates"]} for w in workers}}
json.dump(out, open(os.path.join(E, "analysis.json"), "w"), indent=1, default=str)

# ------------------------------------------------------------------ summary
print("== Q1 per worker: entries/min, distinct ids, exc median s, <30s, <2s, stay med s, share88, steps/s")
for w in workers:
    r = Q1[w]
    print(f"{w} {r['entries_88_per_min']:6.1f} {r['distinct_88_ids']:5d}/{r['entries_88']:<5d} "
          f"{r['excursion_seconds']['median']:.3f} {r['excursions_shorter_than_30s']:.4f} {r['excursions_shorter_than_2s']:.3f} "
          f"{r['stay_88_seconds']['median']:.2f} {r['time_share_by_gates'].get('88', 0):.2f} {r['steps_per_s']} below88={r['below_88']}")
print("pooled:", json.dumps(Q1_pooled, default=str)[:1500])
print("== Q2 v3:", json.dumps(Q2["pooled"]))
for w in workers:
    print(w, json.dumps(Q2["per_worker"][w]))
print("== Q2 exact coincidences:", json.dumps({k: v for k, v in Q2b.items() if k != "examples"}))
print("== Q2 exact hops:", json.dumps({k: v for k, v in Q2a.items() if k != "examples"}))
print("== Q3:", json.dumps({k: v for k, v in Q3.items() if k not in ("same_start_detail", "cross_pair_detail")}))
for d in Q3["same_start_detail"]:
    print("  same-start", json.dumps(d)[:600])
print("  top cross pairs", json.dumps(Q3["cross_pair_detail"][:6]))
print("== Q4:", json.dumps({k: v for k, v in Q4.items() if k != "per_worker"}))
for w in workers:
    print(w, json.dumps(Q4["per_worker"][w]))
