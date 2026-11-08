#!/usr/bin/env python3
"""exp2 analysis, measurements (a)-(c) of DESIGN.md (and the summary of (d) from exact.jsonl).

Distance between two 88 states: Jaccard distance of the helper sets (values minus the 32 target
rows), minimised over the 4 byte rotations. State of a chain at time t: its latest 88 state
(entry `v` or departure `xv`) at or before t.

usage: analyze_exp2.py [T_END_S]  (default: up to the end of the logs) -> analysis.json, analysis.out
"""
import glob, json, os, random, sys
from collections import defaultdict
import numpy as np
from scipy import sparse
from scipy.stats import spearmanr

sys.path.insert(0, os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/translog"))
import plateau_sig as ps  # noqa: E402

E = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/translog/exp2")
RUNS = os.path.join(E, "runs/E2/workers")
T_END = float(sys.argv[1]) if len(sys.argv) > 1 else None
TSET = set(ps.sp.tset)
N_EFF = 1.3e5
TICK = 300.0
WIN = 900.0
THIN = 5.0
MASK = (1 << 32) - 1
out_lines = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out_lines.append(s)


def rot(v, s):
    return ((v << s) | (v >> (32 - s))) & MASK if s else v


def group(w):
    return w.split("-")[0]


# ------------------------------------------------------------------ load
sigc = json.load(open(os.path.join(E, "sigcache.json"))) if os.path.exists(os.path.join(E, "sigcache.json")) else {}
W = {}
for f in sorted(glob.glob(os.path.join(RUNS, "*/translog.jsonl"))):
    w = os.path.basename(os.path.dirname(f))
    states = []        # (t, kind, id, helpers frozenset)
    entries = []       # (t, id)
    start = None
    t_last = 0.0
    n_rows = 0
    below = 0
    for line in open(f):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r.get("k") not in ("step", "chain"):
            continue
        t = r["t"]
        if T_END is not None and t > T_END:
            break
        n_rows += 1
        t_last = t
        if r["g"] < 88:
            below += 1
        if r["g"] <= 88 and r.get("v"):
            h = frozenset(v for v in r["v"] if v not in TSET)
            states.append((t, "e", r.get("id"), h))
            entries.append((t, r.get("id")))
            if start is None:
                start = h
        if "xv" in r:
            states.append((t, "x", r.get("xid"), frozenset(v for v in r["xv"] if v not in TSET)))
    W[w] = {"states": states, "entries": entries, "start": start, "t_last": t_last, "rows": n_rows,
            "below88": below}
workers = sorted(W)
t_end = min(W[w]["t_last"] for w in workers)
if T_END is not None:
    t_end = min(t_end, T_END)
say(f"workers {len(workers)}; common log end t = {t_end:.0f} s")
for w in workers:
    d = W[w]
    say(f"  {w}: rows {d['rows']}, 88 entries {len(d['entries'])}, departures "
        f"{sum(1 for s in d['states'] if s[1] == 'x')}, distinct ids {len({i for _, i in d['entries']})}, "
        f"rows below 88 {d['below88']}, helpers per state {sorted({len(s[3]) for s in d['states']})[:3]}")


def jd_rot(a, b):
    best = 1.0
    for s in (0, 8, 16, 24):
        bb = b if s == 0 else frozenset(rot(v, s) for v in b)
        i = len(a & bb)
        u = len(a) + len(bb) - i
        dd = 1 - i / u if u else 0.0
        if dd < best:
            best = dd
    return best


def current(w, t):
    """latest state at or before t (binary search over the time-sorted list)."""
    st = W[w]["states"]
    lo, hi = 0, len(st)
    while lo < hi:
        mid = (lo + hi) // 2
        if st[mid][0] <= t:
            lo = mid + 1
        else:
            hi = mid
    return st[lo - 1][3] if lo else W[w]["start"]


ticks = [TICK * k for k in range(1, int(t_end // TICK) + 1)]
res = {"t_end": t_end, "ticks": ticks}

# ------------------------------------------------------------------ (a) same-start drift, (b) wander
pairs_same = [(f"{g}-00", f"{g}-01") for g in sorted({group(w) for w in workers})]
pairs_cross = [(a, b) for i, a in enumerate(workers) for b in workers[i + 1:] if group(a) != group(b)]
A = {}
for a, b in pairs_same:
    A[f"{a}/{b}"] = [round(jd_rot(current(a, t), current(b, t)), 4) for t in ticks]
B = {w: [round(jd_rot(current(w, t), W[w]["start"]), 4) for t in ticks] for w in workers}
Ccur = {f"{a}/{b}": [round(jd_rot(current(a, t), current(b, t)), 4) for t in ticks] for a, b in pairs_cross}
seed_d = {f"{a}/{b}": round(jd_rot(W[a]["start"], W[b]["start"]), 4) for a, b in pairs_cross}
res["a_same_current"] = A
res["b_wander"] = B
res["c_cross_current"] = Ccur
res["seed_dist_cross"] = seed_d
say("\n(a) same-start pair distance of current 88 states, every 5 min (helper Jaccard, min over rotations)")
say("  t(min) " + " ".join(f"{int(t / 60):>5}" for t in ticks))
for k, v in A.items():
    say(f"  {k:13s}" + " ".join(f"{x:5.2f}" for x in v))
say("(b) distance of each chain's current state to its own start")
for k, v in B.items():
    say(f"  {k:13s}" + " ".join(f"{x:5.2f}" for x in v))
say("cross-seed current-state distance (median / min over the 24 cross pairs)")
med = [float(np.median([Ccur[k][i] for k in Ccur])) for i in range(len(ticks))]
mn = [min(Ccur[k][i] for k in Ccur) for i in range(len(ticks))]
say("  median       " + " ".join(f"{x:5.2f}" for x in med))
say("  min          " + " ".join(f"{x:5.2f}" for x in mn))
say(f"  seed-to-seed distances (cross groups): min {min(seed_d.values()):.3f} median {np.median(list(seed_d.values())):.3f}")
res["c_cross_current_median"] = med
res["c_cross_current_min"] = mn

# ------------------------------------------------------------------ (c) minimum cross-seed distance on thinned visited sets
thin = {}
for w in workers:
    seen_bins = set()
    rows = []
    for t, kind, i, h in W[w]["states"]:
        if t > t_end:
            break
        b = int(t // THIN)
        if b in seen_bins:
            continue
        seen_bins.add(b)
        rows.append((t, h))
    thin[w] = rows
vocab = {}
for w in workers:
    for t, h in thin[w]:
        for v in h:
            for s in (0, 8, 16, 24):
                vocab.setdefault(rot(v, s), len(vocab))


def mat(rows, s):
    data, ri, ci = [], [], []
    for r, (t, h) in enumerate(rows):
        for v in h:
            ri.append(r)
            ci.append(vocab[rot(v, s)])
            data.append(1.0)
    return sparse.csr_matrix((data, (ri, ci)), shape=(len(rows), len(vocab)), dtype=np.float32)


M0 = {w: mat(thin[w], 0) for w in workers}
Mr = {w: [M0[w]] + [mat(thin[w], s) for s in (8, 16, 24)] for w in workers}
size = {w: np.array([len(h) for t, h in thin[w]], dtype=np.float32) for w in workers}
times = {w: np.array([t for t, h in thin[w]]) for w in workers}


def dist_matrix(a, b):
    best = None
    for s in range(4):
        inter = (M0[a] @ Mr[b][s].T).toarray()
        union = size[a][:, None] + size[b][None, :] - inter
        d = 1 - inter / union
        best = d if best is None else np.minimum(best, d)
    return best


nwin = int(np.ceil(t_end / WIN))
win_min = {}
cum_min = {}
shuffle_gap = {}
rng = random.Random(20261110)


def window_stats(a, b):
    D = dist_matrix(a, b)
    wa = np.minimum((times[a] // WIN).astype(int), nwin - 1)
    wb = np.minimum((times[b] // WIN).astype(int), nwin - 1)
    wm = []
    for k in range(nwin):
        ia, ib = np.where(wa == k)[0], np.where(wb == k)[0]
        wm.append(float(D[np.ix_(ia, ib)].min()) if len(ia) and len(ib) else None)
    # cumulative min at window ends (all states up to the end of window k, any times)
    cm = []
    for k in range(nwin):
        ia, ib = np.where(wa <= k)[0], np.where(wb <= k)[0]
        cm.append(float(D[np.ix_(ia, ib)].min()) if len(ia) and len(ib) else None)
    # shuffled control: permute window labels of the states (same counts), recompute the cumulative curve
    sh = []
    for _ in range(20):
        pa = wa.copy(); pb = wb.copy()
        np.random.default_rng(rng.randrange(1 << 30)).shuffle(pa)
        np.random.default_rng(rng.randrange(1 << 30)).shuffle(pb)
        c2 = []
        for k in range(nwin):
            ia, ib = np.where(pa <= k)[0], np.where(pb <= k)[0]
            c2.append(float(D[np.ix_(ia, ib)].min()) if len(ia) and len(ib) else np.nan)
        sh.append(c2)
    return wm, cm, np.nanmean(np.array(sh), axis=0).tolist(), float(D.min())


say(f"\n(c) minimum distance between visited states (thinned to 1 state / {THIN:.0f} s per chain: "
    + ", ".join(f"{w} {len(thin[w])}" for w in workers) + ")")
overall = {}
for a, b in pairs_cross + pairs_same:
    k = f"{a}/{b}"
    wm, cm, shm, dmin = window_stats(a, b)
    win_min[k], cum_min[k], shuffle_gap[k], overall[k] = wm, cm, shm, dmin
res["c_window_min"] = win_min
res["c_cum_min"] = cum_min
res["c_cum_min_shuffled_mean"] = shuffle_gap
res["c_overall_min"] = overall


def trend(ys):
    xs = [i for i, y in enumerate(ys) if y is not None]
    yy = [y for y in ys if y is not None]
    if len(xs) < 3:
        return None, None
    slope = float(np.polyfit(xs, yy, 1)[0])
    rho = float(spearmanr(xs, yy).correlation) if len(set(yy)) > 1 else 0.0
    return slope, rho


def ftr(s, r):
    return f"  slope {s:+.4f} rho {r:+.2f}" if s is not None else "  (too few windows)"


say(f"  per-{int(WIN / 60)}-min-window minimum distance, windows 1..{nwin}")
rows_c = []
for k in [f"{a}/{b}" for a, b in pairs_cross]:
    s, r = trend(win_min[k])
    rows_c.append((k, s, r))
    say(f"  {k:13s}" + " ".join(f"{x:5.2f}" if x is not None else "    -" for x in win_min[k]) + ftr(s, r))
agg_min = [min(win_min[k][i] for k, _, _ in rows_c if win_min[k][i] is not None) for i in range(nwin)]
agg_med = [float(np.median([win_min[k][i] for k, _, _ in rows_c if win_min[k][i] is not None])) for i in range(nwin)]
s_min, r_min = trend(agg_min)
s_med, r_med = trend(agg_med)
say("  min over 24 cross pairs " + " ".join(f"{x:5.2f}" for x in agg_min) + ftr(s_min, r_min))
say("  median over cross pairs " + " ".join(f"{x:5.2f}" for x in agg_med) + ftr(s_med, r_med))
slopes = [s for _, s, _ in rows_c if s is not None]
if slopes:
    say(f"  per-pair slopes: median {np.median(slopes):+.4f}, {sum(1 for s in slopes if s < 0)} of {len(slopes)} negative")
res["c_window_trend"] = {"min_over_pairs": agg_min, "min_slope": s_min, "min_rho": r_min,
                         "median_over_pairs": agg_med, "median_slope": s_med, "median_rho": r_med,
                         "per_pair": rows_c}
say("  same-start pairs, per-window minimum distance (time-aligned windows)")
for a, b in pairs_same:
    k = f"{a}/{b}"
    say(f"  {k:13s}" + " ".join(f"{x:5.2f}" if x is not None else "    -" for x in win_min[k]))
say("  cumulative minimum (all states up to window end) vs time-shuffled control, min over cross pairs")
cm_all = [min(cum_min[k][i] for k, _, _ in rows_c) for i in range(nwin)]
sh_all = [min(shuffle_gap[k][i] for k, _, _ in rows_c) for i in range(nwin)]
say("  actual   " + " ".join(f"{x:5.2f}" for x in cm_all))
say("  shuffled " + " ".join(f"{x:5.2f}" for x in sh_all))
gap = [float(np.mean([cum_min[k][i] - shuffle_gap[k][i] for k, _, _ in rows_c])) for i in range(nwin)]
say("  mean (actual - shuffled) over cross pairs " + " ".join(f"{x:+.3f}" for x in gap)
    + "  (> 0: later states closer than earlier ones = approach)")
res["c_cum_min_all"] = cm_all
res["c_cum_shuffled_all"] = sh_all
res["c_cum_gap"] = gap
say(f"  overall min cross-seed distance {min(overall[k] for k, _, _ in rows_c):.3f}; per cross pair min: median "
    f"{np.median([overall[k] for k, _, _ in rows_c]):.3f}")
say("  overall min same-start (any times) " + ", ".join(f"{a}/{b} {overall[f'{a}/{b}']:.3f}" for a, b in pairs_same))

# ------------------------------------------------------------------ (c) shared v3 nodes vs null
def shared_at(T):
    nodes = {}
    for w in workers:
        s = set()
        for t, i in W[w]["entries"]:
            if t > T:
                break
            g = sigc.get(i)
            if g:
                s.add(g)
        nodes[w] = s
    missing = sum(1 for w in workers for t, i in W[w]["entries"] if t <= T and i not in sigc)
    starts = {w: sigc.get(W[w]["entries"][0][1]) if W[w]["entries"] else None for w in workers}
    out = {"T": T, "missing_sigs": missing, "distinct": {w: len(nodes[w]) for w in workers}}
    for name, prs, excl_start in (("cross", pairs_cross, False), ("same", pairs_same, True)):
        P = 0
        inc = 0
        nodeset = set()
        per = {}
        for a, b in prs:
            na, nb = set(nodes[a]), set(nodes[b])
            if excl_start:
                na.discard(starts[a]); nb.discard(starts[a]); na.discard(starts[b]); nb.discard(starts[b])
            P += len(na) * len(nb)
            sh = na & nb
            inc += len(sh)
            nodeset |= sh
            per[f"{a}/{b}"] = len(sh)
        lam = P / N_EFF
        lo, hi = lam - 1.96 * lam ** 0.5, lam + 1.96 * lam ** 0.5
        out[name] = {"P": P, "expected": lam, "poisson95": [max(0.0, lo), hi], "M_incidences": inc,
                     "M_nodes": len(nodeset), "per_pair": per}
    # exact-state identities shared across groups
    ids = {w: {i for t, i in W[w]["entries"] if t <= T} for w in workers}
    out["shared_ids_cross"] = sum(len(ids[a] & ids[b]) for a, b in pairs_cross)
    out["shared_ids_same"] = sum(len(ids[a] & ids[b]) for a, b in pairs_same)
    return out


say("\n(c) shared v3 nodes vs the null (N_eff = 1.3e5)")
res["c_shared"] = []
for T in sorted({min(3600.0, t_end), t_end}):
    o = shared_at(T)
    res["c_shared"].append(o)
    say(f"  up to t = {T:.0f} s (missing sigs {o['missing_sigs']}); distinct v3 per chain {o['distinct']}")
    for name in ("cross", "same"):
        c = o[name]
        say(f"    {name}: P = {c['P']:,}, expected {c['expected']:.2f} (95 % [{c['poisson95'][0]:.1f}, "
            f"{c['poisson95'][1]:.1f}]), M = {c['M_incidences']} pair incidences / {c['M_nodes']} nodes; "
            f"per pair {c['per_pair'] if name == 'same' else {k: v for k, v in c['per_pair'].items() if v}}")
    say(f"    shared exact-state ids: cross {o['shared_ids_cross']}, same-start {o['shared_ids_same']}")

# ------------------------------------------------------------------ calibration of the distance scale
# (not pre-registered, added at the 30 min interim to read (a)-(c)): the helper distance between
# two states with the SAME v3 node (same-start pairs: first state of each chain on the node), and
# between consecutive entry states of one chain.
first_state = {w: {} for w in workers}
for w in workers:
    hs = {}
    for t, kind, i, h in W[w]["states"]:
        if kind == "e" and t <= t_end:
            g = sigc.get(i)
            if g and g not in first_state[w]:
                first_state[w][g] = h
                hs[g] = t
    W[w]["first_t"] = hs
same_node_d = []
meet_win = {}
for a, b in pairs_same:
    mw = [0] * nwin
    for g in set(first_state[a]) & set(first_state[b]):
        same_node_d.append(jd_rot(first_state[a][g], first_state[b][g]))
        tm = max(W[a]["first_t"][g], W[b]["first_t"][g])   # when the node became shared
        mw[min(int(tm // WIN), nwin - 1)] += 1
    meet_win[f"{a}/{b}"] = mw
res["same_meetings_by_window"] = meet_win
say(f"\nsame-start shared v3 nodes by {int(WIN / 60)}-min window in which the node became shared (incl. start node)")
for k, v in meet_win.items():
    say(f"  {k:13s}" + " ".join(f"{x:5d}" for x in v))
consec = []
for w in workers:
    es = [h for t, kind, i, h in W[w]["states"] if kind == "e" and t <= t_end]
    consec += [jd_rot(es[k], es[k + 1]) for k in range(0, len(es) - 1, max(1, len(es) // 300))]


def qs(xs):
    return [round(float(np.quantile(xs, p)), 3) for p in (0, 0.1, 0.5, 0.9, 1)] if xs else None


say("\ncalibration (added at interim): helper distance quantiles [min, p10, med, p90, max]")
say(f"  same v3 node, two same-start chains (n = {len(same_node_d)}): {qs(same_node_d)}")
say(f"  consecutive entries of one chain (n = {len(consec)}): {qs(consec)}")
res["calib_same_node"] = qs(same_node_d)
res["calib_consecutive"] = qs(consec)

# ------------------------------------------------------------------ (d) summary of exact.jsonl
ex = [json.loads(l) for l in open(os.path.join(E, "exact.jsonl"))] if os.path.exists(os.path.join(E, "exact.jsonl")) else []
dsum = defaultdict(lambda: defaultdict(int))
for r in ex:
    key = "b_in_a" if r["test"] != "hop" else "entry_in_dep"
    v = r.get(key)
    outcome = "timeout" if r.get("error") == "timeout" else ("error" if r.get("error") else
                                                              ("yes" if v else "no"))
    dsum[r["test"]][outcome] += 1
    if r["test"] == "hop":
        dsum["hop_v3_changed"][str(r.get("sig_dep") != r.get("sig_entry"))] += 1
        if v is not None:
            dsum["hop_v3_changed_and_" + outcome][str(r.get("sig_dep") != r.get("sig_entry"))] += 1
sizes = sorted({(r.get("size"), str(r.get("radices"))) for r in ex if r.get("size")})
res["d_exact"] = {k: dict(v) for k, v in dsum.items()}
res["d_sizes"] = sizes[:40]
say("\n(d) exact tests (pes_lib.compress, 60 s cap):", json.dumps(res["d_exact"]))
hops = [r for r in ex if r["test"] == "hop"]
if hops:
    say(f"  hop sample: worker {hops[0]['worker']}, t {hops[0]['t_dep']:.0f}-{hops[-1]['t_entry']:.0f} s, "
        f"{len(hops)} hops; departure==entry exact state {sum(r['same_state'] for r in hops)}; "
        f"median |xv ^ entry| {int(np.median([r['sym_diff'] for r in hops]))}")
    say(f"  plateau sizes met: {sizes[:12]}")
json.dump(res, open(os.path.join(E, "analysis.json"), "w"), indent=1, default=str)
open(os.path.join(E, "analysis.out"), "w").write("\n".join(out_lines) + "\n")
