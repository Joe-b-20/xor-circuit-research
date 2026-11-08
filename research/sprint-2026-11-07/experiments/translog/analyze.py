#!/usr/bin/env python3
"""Analyse a transition log (and the paired 30 s sampler, and the T0/T1 overhead).

Usage: analyze.py [RUNS_DIR] [SAMPLES.jsonl]      (defaults: ./runs, ./samples/samples.jsonl)
Writes analysis.json next to the runs directory and prints a summary.

Definitions.  A *segment* is the stretch between two consecutive log rows (chain or step):
the chain sits at ``g`` gates from the row's (it, t) to the next row's.  An *88 entry* is a
segment at 88 gates; an *excursion* is the gap between two consecutive 88 segments of the same
chain (from leaving 88 to re-entering it); its *height* is the largest gate count seen inside.
``t`` is the campaign clock (seconds since the run started), the same clock as chain.json's
``t`` that the sampler copies, so sampler records are matched to segments on ``t``.
"""
import hashlib
import json
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "runs"
SAMPLES = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "samples" / "samples.jsonl"
PERIOD = 30.0


def med(xs, fmt="{:.1f}"):
    return fmt.format(st.median(xs)) if xs else "n/a"


def q(xs, p):
    if not xs:
        return float("nan")
    xs = sorted(xs)
    k = max(0, min(len(xs) - 1, int(round(p * (len(xs) - 1)))))
    return xs[k]


def load_rows(path):
    rows = [json.loads(line) for line in open(path)]
    meta = {"open": None, "close": None}
    body = []
    for r in rows:
        if r["k"] in ("open", "close"):
            meta[r["k"]] = r
        else:
            body.append(r)
    return meta, body


def worker_dirs(arm):
    return sorted((RUNS / arm / "workers").glob("*"))


def overhead():
    out = {}
    for arm in ("T0", "T1"):
        for w in worker_dirs(arm):
            status = json.load(open(w / "status.json"))
            stop = None
            for line in open(w / "events.jsonl"):
                if '"ev":"stop"' in line:
                    stop = json.loads(line)
            steps, t = status["steps"], status["t"]
            rec = {"steps": steps, "t": round(t, 1), "steps_per_s": round(steps / t, 2),
                   "accepted": status["accepted"],
                   "cpu_s": None if stop is None else round(stop["cpu_s"], 1),
                   "wall_s": None if stop is None else round(stop["wall_s"], 1),
                   "steps_per_cpu_s": None if stop is None else round(steps / stop["cpu_s"], 2),
                   "engine": status["engine"]}
            tl = w / "translog.jsonl"
            if tl.exists():
                rec["translog_bytes"] = tl.stat().st_size
                meta, _ = load_rows(tl)
                rec["translog_close"] = meta["close"]
            out[arm] = rec
    if "T0" in out and "T1" in out:
        a, b = out["T0"], out["T1"]
        out["ratio_steps_per_s_T1_over_T0"] = round(b["steps_per_s"] / a["steps_per_s"], 4)
        if a["steps_per_cpu_s"] and b["steps_per_cpu_s"]:
            out["ratio_steps_per_cpu_s_T1_over_T0"] = round(b["steps_per_cpu_s"] / a["steps_per_cpu_s"], 4)
        c = b.get("translog_close") or {}
        if c.get("seconds") is not None and b["cpu_s"]:
            out["translog_self_timed_share"] = round(c["seconds"] / b["cpu_s"], 5)
    return out


def analyse_log(path, t_end):
    meta, rows = load_rows(path)
    rows.sort(key=lambda r: (r["it"], r["t"]))
    close = meta["close"]
    if close is not None:
        t_end = close["t"]
    # segments
    segs = []
    for i, r in enumerate(rows):
        nxt = rows[i + 1] if i + 1 < len(rows) else None
        segs.append({"g": r["g"], "d": r["d"], "it0": r["it"], "t0": r["t"],
                     "it1": nxt["it"] if nxt else None, "t1": nxt["t"] if nxt else t_end,
                     "k": r["k"], "m": r["m"], "c": r["c"], "id": r.get("id"), "v": r.get("v"),
                     "w": r["w"]})
    res = {"rows": len(rows), "span_s": round(t_end - rows[0]["t"], 1) if rows else 0,
           "chains": len({r["c"] for r in rows}),
           "chain_rows": sum(1 for r in rows if r["k"] == "chain")}
    steps = [r for r in rows if r["k"] == "step"]
    res["step_transitions"] = len(steps)
    res["transitions_per_s"] = round(len(steps) / res["span_s"], 3) if res["span_s"] else None
    res["transition_pairs"] = {f"{r['p']}->{r['g']}": n for (r, n) in
                               [(None, 0)] and sorted(Counter((s["p"], s["g"]) for s in steps).items())
                               for r in [{"p": r[0], "g": r[1]}]} if steps else {}
    res["moves_into_88"] = dict(Counter(s["m"] for s in steps if s["g"] == 88).most_common())
    res["moves_out_of_88"] = dict(Counter(s["m"] for s in steps if s["p"] == 88).most_common())
    # time share by level
    share = defaultdict(float)
    for s in segs:
        share[s["g"]] += (s["t1"] - s["t0"]) if s["t1"] is not None else 0.0
    tot = sum(share.values()) or 1.0
    res["time_share_by_gates"] = {str(g): round(share[g] / tot, 4) for g in sorted(share)}
    res["below_88_segments"] = [s for s in segs if s["g"] < 88]
    # 88 segments / entries
    e88 = [s for s in segs if s["g"] == 88]
    res["entries_88"] = len(e88)
    res["entries_88_by_step"] = sum(1 for s in e88 if s["k"] == "step")
    res["entries_88_per_min"] = round(len(e88) / res["span_s"] * 60, 2) if res["span_s"] else None
    stay_s = [s["t1"] - s["t0"] for s in e88 if s["t1"] is not None]
    stay_it = [s["it1"] - s["it0"] for s in e88 if s["it1"] is not None]
    res["stay_88_seconds"] = {"median": q(stay_s, .5), "q1": q(stay_s, .25), "q3": q(stay_s, .75),
                              "max": max(stay_s) if stay_s else None}
    res["stay_88_steps"] = {"median": q(stay_it, .5), "q1": q(stay_it, .25), "q3": q(stay_it, .75),
                            "max": max(stay_it) if stay_it else None}
    res["depth_at_88_entry"] = dict(sorted(Counter(s["d"] for s in e88).items()))
    # identities
    ids = Counter(s["id"] for s in e88 if s["id"])
    res["distinct_88_ids"] = len(ids)
    rec = {i: n for i, n in ids.items() if n > 1}
    res["recurring_ids"] = len(rec)
    res["entries_on_recurring_ids"] = sum(rec.values())
    immediate = 0
    later = []
    last_seen = {}
    prev_id = None
    for k, s in enumerate(e88):
        i = s["id"]
        if i in last_seen:
            if prev_id == i:
                immediate += 1
            else:
                later.append({"gap_entries": k - last_seen[i], "gap_s": round(s["t0"] - e88[last_seen[i]]["t0"], 1)})
        last_seen[i] = k
        prev_id = i
    res["recurrence_immediate_return"] = immediate
    res["recurrence_after_other_states"] = len(later)
    res["recurrence_examples"] = later[:10]
    # locality between consecutive 88 entries (values, no rotation)
    jac, changed = [], []
    for a, b in zip(e88, e88[1:]):
        if a["v"] and b["v"]:
            A, B = set(a["v"]), set(b["v"])
            jac.append(1 - len(A & B) / len(A | B))
            changed.append(len(A - B))
    res["consecutive_entry_jaccard_distance"] = {"median": round(q(jac, .5), 3), "q1": round(q(jac, .25), 3),
                                                 "q3": round(q(jac, .75), 3)} if jac else None
    res["consecutive_entry_values_replaced"] = {"median": q(changed, .5), "q1": q(changed, .25),
                                                "q3": q(changed, .75), "zero": changed.count(0)} if changed else None
    # excursions
    exc = []
    for a, b in zip(e88, e88[1:]):
        if a["c"] != b["c"] or a["t1"] is None:
            continue
        inside = [s for s in segs if s["t0"] >= a["t1"] and s["t0"] < b["t0"] and s["c"] == a["c"]]
        height = max([s["g"] for s in inside] + [89])
        exc.append({"steps": b["it0"] - a["it1"], "s": b["t0"] - a["t1"], "h": height,
                    "t_leave": a["t1"], "t_back": b["t0"], "same_id": a["id"] == b["id"]})
    res["excursions"] = len(exc)
    xs = [e["s"] for e in exc]
    xi = [e["steps"] for e in exc]
    res["excursion_seconds"] = {"median": q(xs, .5), "q1": q(xs, .25), "q3": q(xs, .75), "p90": q(xs, .9),
                                "max": max(xs) if xs else None, "mean": round(st.mean(xs), 2) if xs else None}
    res["excursion_steps"] = {"median": q(xi, .5), "q1": q(xi, .25), "q3": q(xi, .75), "p90": q(xi, .9),
                              "max": max(xi) if xi else None}
    res["excursions_shorter_than_30s"] = round(sum(1 for e in exc if e["s"] < PERIOD) / len(exc), 4) if exc else None
    res["excursions_shorter_than_2s"] = round(sum(1 for e in exc if e["s"] < 2.0) / len(exc), 4) if exc else None
    res["excursion_height"] = dict(sorted(Counter(e["h"] for e in exc).items()))
    res["excursions_returning_to_same_state"] = sum(1 for e in exc if e["same_id"])
    # what a 30 s sampler would see: ticks every 30 s from the first row; an excursion is
    # "seen" when a tick falls inside it; an 88 stay is "seen" when a tick falls inside it.
    t_first = rows[0]["t"] if rows else 0.0
    ticks = []
    t = t_first + PERIOD
    while t < t_end:
        ticks.append(t)
        t += PERIOD
    def seen(lo, hi):
        return any(lo <= tk < hi for tk in ticks)
    res["sim_ticks"] = len(ticks)
    res["sim_excursions_with_a_tick"] = sum(1 for e in exc if seen(e["t_leave"], e["t_back"]))
    res["sim_stays88_with_a_tick"] = sum(1 for s in e88 if s["t1"] is not None and seen(s["t0"], s["t1"]))
    res["sim_fraction_excursions_missed"] = round(1 - res["sim_excursions_with_a_tick"] / len(exc), 4) if exc else None
    res["sim_fraction_stays88_missed"] = round(1 - res["sim_stays88_with_a_tick"] / len(e88), 4) if e88 else None
    return res, segs, e88


def pair_sampler(samples_path, arm, worker, segs, e88):
    """Match the real sampler's records for this worker to the log's segments."""
    if not samples_path.exists():
        return {"note": "no samples file"}
    recs = [json.loads(l) for l in open(samples_path)]
    mine = [r for r in recs if r["arm"] == arm and r["worker"] == worker]
    out = {"records": len(mine), "records_88": sum(1 for r in mine if r["gates"] == 88),
           "records_89": sum(1 for r in mine if r["gates"] == 89),
           "records_other": sum(1 for r in mine if r["gates"] not in (88, 89))}
    by_t = sorted(segs, key=lambda s: s["t0"])
    matched, exact = set(), 0
    for r in mine:
        if r["gates"] != 88:
            continue
        t = r["t"]
        seg = None
        for s in by_t:
            if s["t0"] <= t and (s["t1"] is None or t < s["t1"]):
                seg = s
        if seg is not None and seg["g"] == 88:
            matched.add(seg["it0"])
            if seg["v"] is not None and sorted(seg["v"]) == sorted(r["values"]):
                exact += 1
    out["distinct_88_stays_sampled"] = len(matched)
    out["of_88_stays"] = len(e88)
    out["sampled_values_equal_entry_values"] = exact
    hashes = {r["hash"] for r in mine if r["gates"] == 88}
    out["distinct_88_sample_hashes"] = len(hashes)
    return out


def main():
    result = {"overhead": overhead(), "logs": {}}
    for arm in ("T1", "T0"):
        for w in worker_dirs(arm):
            tl = w / "translog.jsonl"
            if not tl.exists():
                continue
            status = json.load(open(w / "status.json"))
            res, segs, e88 = analyse_log(tl, status["t"])
            res["sampler"] = pair_sampler(SAMPLES, arm, w.name, segs, e88)
            result["logs"][f"{arm}/{w.name}"] = res
    out = HERE / "analysis.json"
    out.write_text(json.dumps(result, indent=1, default=str))
    print(json.dumps(result, indent=1, default=str))
    print("written", out)


if __name__ == "__main__":
    main()
