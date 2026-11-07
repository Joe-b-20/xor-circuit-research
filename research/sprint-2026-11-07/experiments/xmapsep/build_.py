#!/usr/bin/env python3
"""xmapsep: per-trial table for the 27 sprint trials (X1 8 maps, pt 7 maps, sweep 12 maps).
Reads only: run dirs (plan.json, workers/*/events.jsonl, status.json), prior-run plan.json files,
the pre-harvest circuit list (git ls-tree d281a78^), search/seeds NIST files, crossmap/props.csv.
Writes trials.csv, workers.csv, prior_wh.csv, series/<trial>.txt. No search is run."""
import csv, json, os, re, sys, collections

HOME = os.path.expanduser("~")
S = os.path.join(HOME, "xs-campaigns/2026-11-07-sprint")
REPO = os.path.join(HOME, "xor-circuit-research")
OUT = os.path.join(S, "xmapsep")
XS = os.path.join(HOME, "xs-campaigns")

SPRINT_RUNS = [("x1a", "x1/runs/x1a"), ("x1b", "x1/runs/x1b"), ("pt1", "predtest/runs/pt1"),
               ("pt2", "predtest/runs/pt2"), ("sw1", "sweep/runs/sw1"), ("sw2", "sweep/runs/sw2")]
PRIOR_RUNS = ["2026-10-28/runs/fox_mu8", "2026-10-29/runs/fox_mu8", "2026-10-30-gap/run",
              "2026-10-30-nist/runs/nist-aria", "2026-10-30-nist/runs/nist-twofish",
              "2026-10-30-nist/runs/nist-grostl", "2026-10-30-nist/runs/nist-clefia-m1",
              "2026-10-30-nist/runs/nist-batch-64", "2026-10-30-nist/runs/nist-batch-32a",
              "2026-10-30-nist/runs/nist-batch-32b", "2026-10-30-nist/runs/nist-batch-16a",
              "2026-10-30-nist/runs/nist-batch-16b", "2026-10-31-long/runs/gaps16",
              "2026-10-31-long/runs/wide64"]
ALIAS = {"fox_mu8": "fox-mu8", "fox_mu4": "fox-mu4"}

# ---------------------------------------------------------------- repo state before the harvest
pre = collections.defaultdict(list)   # map -> [(g, d)]
for line in open(os.path.join(OUT, "pre_harvest_circuits.txt")):
    m = re.match(r"circuits/([^/]+)/.*-xor(\d+)-depth(\d+)\.circ\.txt", line.strip())
    if m:
        pre[m.group(1)].append((int(m.group(2)), int(m.group(3))))
nist = collections.defaultdict(list)
for mp in os.listdir(os.path.join(REPO, "search/seeds")):
    d = os.path.join(REPO, "search/seeds", mp)
    if os.path.isdir(d):
        for f in os.listdir(d):
            m = re.match(r"nist-g(\d+)-d(\d+)\.json$", f)
            if m:
                nist[mp].append((int(m.group(1)), int(m.group(2))))
nist["aes-mixcolumns"] = [(97, 3), (90, 4), (88, 5), (92, 6)]  # circuits/README.md
props = {}
for r in csv.DictReader(open(os.path.join(S, "crossmap/props.csv"))):
    props[r["map"]] = r


def best_le(points, cap):
    c = [p for p in points if p[1] <= cap]
    return min(c) if c else None   # (gates, depth) with the fewest gates; ties -> shallower


# ---------------------------------------------------------------- prior worker-hours per map
def load_plan(run_dir):
    p = os.path.join(run_dir, "plan.json")
    return json.load(open(p)) if os.path.exists(p) else None


def plan_workers(plan):
    """yield (target, cap, hours) per worker of a plan; cap None = uncapped; cap may be a list."""
    dur = plan.get("duration")
    ws = plan.get("workers")
    if ws:
        for w in ws:
            yield ALIAS.get(w.get("target"), w.get("target")), w.get("depth_cap"), (dur or 0) / 3600.0
        return
    for g in plan.get("groups", []):
        for _ in range(g.get("count", 1)):
            yield ALIAS.get(g.get("target"), g.get("target")), g.get("depth_cap"), (dur or 0) / 3600.0


prior = []   # rows: run, created, target, cap, hours
for rel in PRIOR_RUNS:
    plan = load_plan(os.path.join(XS, rel))
    if plan is None:
        print("no plan", rel, file=sys.stderr)
        continue
    name = plan.get("name") or rel
    created = plan.get("created_utc", "")
    for t, cap, h in plan_workers(plan):
        prior.append(dict(run=name, created=created, target=t, cap=cap, hours=h))
# v3 run joltik-depth-foxmu8-15 (circuits/SEARCH-TIME.md: 2026-10-27, 22.2 h x 15 workers, shared with
# joltik; no plan.json in ~/xs-campaigns). Its kept circuits are 599@7 and 539@8, so caps 7-8 [guess];
# entered as 166 worker-h (half of 332) split over caps 7 and 8.
prior.append(dict(run="joltik-depth-foxmu8-15 (v3; SEARCH-TIME.md; caps 7/8 guessed)", created="2026-10-27T15:03",
                  target="fox-mu8", cap=[7, 8], hours=166.0))
sprint_plan_rows = []
for tag, rel in SPRINT_RUNS:
    plan = load_plan(os.path.join(S, rel))
    for t, cap, h in plan_workers(plan):
        sprint_plan_rows.append(dict(run=tag, created=plan.get("created_utc", ""), target=t, cap=cap, hours=h))
with open(os.path.join(OUT, "prior_wh.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["run", "created", "target", "cap", "hours"])
    w.writeheader()
    for r in prior + sprint_plan_rows:
        w.writerow(r)


def caps_of(c):
    if isinstance(c, list):
        return [None if x in ("none", None) else int(x) for x in c]
    return [None if c in ("none", None) else int(c)]


def prior_hours(target, cap, before_tag):
    """worker-hours on target before sprint run before_tag: exact cap, cap within 1, free, cap>=, total."""
    rows = [r for r in prior if r["target"] == target]
    order = [t for t, _ in SPRINT_RUNS]
    for r in sprint_plan_rows:
        if r["target"] == target and order.index(r["run"]) < order.index(before_tag):
            rows.append(r)
    ex = b1 = fr = ge = tot = 0.0
    for r in rows:
        cs = caps_of(r["cap"])
        h = r["hours"] / len(cs)
        for c in cs:
            tot += h
            if c is None:
                fr += h; ge += h
            else:
                if c == cap: ex += h
                if abs(c - cap) <= 1: b1 += h
                if c >= cap: ge += h
    runs = sorted({r["run"].split(" ")[0] for r in rows})
    return dict(wh_cap=ex, wh_cap1=b1, wh_free=fr, wh_ge=ge, wh_total=tot, n_prior_runs=len(runs), prior_runs=";".join(runs))


# ---------------------------------------------------------------- per-worker event parsing
def seed_points(plan, w):
    """[(kind, gates, depth)] for the worker's group seeds."""
    grp = next(g for g in plan["groups"] if g["name"] == w["group"])
    pts = []
    for s in grp["seeds"]:
        if s == "root":
            pts.append(("root", None, None))
        elif s == "target":
            pts.append(("nist", None, None))
        else:
            m = re.search(r"-g(\d+)-d(\d+)\.json$", s)
            pts.append(("ours", int(m.group(1)), int(m.group(2))))
    return pts


def parse_worker(run_dir, wid, cap, start_gates=None):
    ev = os.path.join(run_dir, "workers", wid, "events.jsonl")
    imps = []
    restarts = 0
    last_it = 0; last_t = 0.0
    sources = collections.Counter()
    for line in open(ev):
        e = json.loads(line)
        if e["ev"] == "improve":
            imps.append(e)
            sources[str(e.get("root_source"))] += 1
            if e.get("donor"):
                sources["donor:" + str(e.get("donor"))[:20]] += 1
        elif e["ev"] == "restart":
            restarts += 1
            sources["restart:" + str(e.get("source"))] += 1
        if e.get("it") is not None:
            last_it = e["it"]; last_t = e["t"]
    st = json.load(open(os.path.join(run_dir, "workers", wid, "status.json")))
    frontier = [tuple(x) for x in st.get("frontier", [])]
    series = []      # (t, gates, depth, move, root_source): each time the worker's best at <= cap drops below its start
    bestc = start_gates
    for e in imps:
        a = e["after"]
        if a["depth"] <= cap and (bestc is None or a["gates"] < bestc):
            bestc = a["gates"]
            series.append((e["t"], a["gates"], a["depth"], e["move"], e.get("root_source")))
    return dict(status=st, frontier=frontier, series=series, n_imp=len(imps), restarts=restarts, sources=dict(sources),
                it=last_it, t_end=last_t, it_rate=(last_it / last_t if last_t else None))


def quarter_gains(series, ref, dur):
    """gates removed below ref (repo best) in each quarter of the run, from a running-min series."""
    q = [0, 0, 0, 0]
    cur = ref
    for t, g in series:
        if g < cur:
            q[min(3, int(4 * t / dur))] += cur - g
            cur = g
    return q


# ---------------------------------------------------------------- trials
trial_rows = []
worker_rows = []
series_dir = os.path.join(OUT, "series")
os.makedirs(series_dir, exist_ok=True)
for tag, rel in SPRINT_RUNS:
    run_dir = os.path.join(S, rel)
    plan = load_plan(run_dir)
    dur = plan["duration"]
    bymap = collections.defaultdict(list)
    for w in plan["workers"]:
        bymap[w["target"]].append(w)
    for target, ws in bymap.items():
        cap = ws[0]["depth_cap"]
        p = props[target]
        k, m = p["k"], p["m"]
        size = f"{k}x{k}/GF(2^{m})"
        cls = "8x8" if k == "8" else "4x4"
        pre_pts = pre[target]
        pre_best = best_le(pre_pts, cap)
        nist_best = best_le(nist[target], cap)
        seeds_desc = set()
        wk = []
        for w in ws:
            # the circuit this worker actually started from (plan.workers[].seed.sha256 -> plan.seeds)
            if w["seed"].get("kind") == "root":
                arm, arm_start, start_pt = "fresh", None, "root"
            else:
                sd = plan["seeds"][w["seed"]["sha256"]]
                src = sd["source"]
                arm = "nist" if src.startswith("target:") else "ours"
                arm_start = sd["gates"] if sd["depth"] <= cap else None
                start_pt = f"{'NIST' if arm == 'nist' else 'ours'} {sd['gates']}@{sd['depth']}"
            r = parse_worker(run_dir, w["id"], cap, arm_start)
            for kind, g, d in seed_points(plan, w):
                if kind == "root":
                    seeds_desc.add("root")
                elif kind == "nist":
                    seeds_desc.add(f"NIST {nist_best[0]}@{nist_best[1]}")
                else:
                    seeds_desc.add(f"ours {g}@{d}")
            fr_le = [x for x in r["frontier"] if x[1] <= cap]
            wbest = min(fr_le) if fr_le else None
            ser = r["series"]
            t_first = next((t for t, g, d, mv, rs in ser if arm_start is not None and g < arm_start), None)
            t_reach = next((t for t, g, d, mv, rs in ser if pre_best and g <= pre_best[0]), None)
            t_gain = next((t for t, g, d, mv, rs in ser if pre_best and g < pre_best[0]), None)
            t_last = ser[-1][0] if ser else None
            wk.append((w, r, arm))
            worker_rows.append(dict(run=tag, map=target, worker=w["id"], arm=arm, cap=cap, start=start_pt, start_gates=arm_start,
                                    best_le_cap=f"{wbest[0]}@{wbest[1]}" if wbest else "-",
                                    best_any=f"{r['status']['best']['gates']}@{r['status']['best']['depth']}",
                                    n_improve=r["n_imp"], n_drops_le_cap=len(ser), restarts=r["restarts"],
                                    t_first_imp_s=None if t_first is None else round(t_first),
                                    t_reach_repo_s=None if t_reach is None else round(t_reach),
                                    t_first_gain_s=None if t_gain is None else round(t_gain),
                                    t_last_drop_s=None if t_last is None else round(t_last),
                                    iters=r["it"], it_per_s=None if r["it_rate"] is None else round(r["it_rate"], 1),
                                    wall_s=round(r["t_end"]), sources=json.dumps(r["sources"])))
            with open(os.path.join(series_dir, f"{tag}-{w['id']}.txt"), "w") as f:
                f.write(f"# {tag} {w['id']} cap {cap} arm {arm} start {arm_start} repo best <=cap {pre_best} NIST {nist_best}\n")
                f.write("# t_s  gates  depth  move  root_source   (each drop of the worker's best at <= cap)\n")
                for t, g, d, mv, rs in ser:
                    f.write(f"{t:8.1f} {g:5d} {d:3d}  {mv:14s} {rs}\n")
                f.write(f"# frontier at end {r['frontier']}; improve events {r['n_imp']}; restarts {r['restarts']}; it {r['it']}\n")
        # trial-level result = union over workers (both arms for X1, both workers for pt)
        fr_all = sorted({x for _, r, _ in wk for x in r["frontier"]})
        res_le = best_le(fr_all, cap)
        res_arm = [arm for _, r, arm in wk if res_le in r["frontier"]]
        gain_cap = (pre_best[0] - res_le[0]) if (pre_best and res_le) else None
        gain_any = None; gain_any_pt = None
        for g, d in fr_all:
            pb = best_le(pre_pts, d)
            if pb:
                dg = pb[0] - g
                if gain_any is None or dg > gain_any:
                    gain_any, gain_any_pt = dg, f"{g}@{d} (was {pb[0]}@{pb[1]})"
        res_depth = res_le[1] if res_le else None
        # how far below NIST (at the cap) the map already was before the trial, and after
        pre_gap = (nist_best[0] - pre_best[0]) / nist_best[0] if (nist_best and pre_best) else None
        post_gap = (nist_best[0] - res_le[0]) / nist_best[0] if (nist_best and res_le) else None
        # depth drift of the earlier (mostly uncapped) search: depth of our pre-trial best at any depth minus the cap
        any_best = min(pre_pts) if pre_pts else None
        drift = (any_best[1] - cap) if any_best else None
        near = min((abs(d - res_depth) for g, d in pre_pts), default=None) if res_depth is not None else None
        slack = (cap - pre_best[1]) if pre_best else None
        ph = prior_hours(target, cap, tag)
        # merged own-best series over the trial's seeded workers (fresh arms excluded: their own best
        # starts hundreds of gates above the seed and says nothing about the seed's slack)
        seeded = [(w, r, arm) for w, r, arm in wk if arm != "fresh"]
        merged = sorted((t, g) for _, r, _ in seeded for t, g, d, mv, rs in r["series"])
        own = []; cur = None
        for t, g in merged:
            if cur is None or g < cur:
                cur = g; own.append((t, g))
        t_last_own = own[-1][0] if own else None
        q = quarter_gains(own, pre_best[0], dur) if pre_best else [0, 0, 0, 0]
        # the same with the fresh arm included (X1 ss16 gain came from the fresh arm)
        merged_all = sorted((t, g) for _, r, _ in wk for t, g, d, mv, rs in r["series"])
        all_own = []; cur = None
        for t, g in merged_all:
            if cur is None or g < cur:
                cur = g; all_own.append((t, g))
        qa = quarter_gains(all_own, pre_best[0], dur) if pre_best else [0, 0, 0, 0]
        t_last_gain = max((t for t, g in all_own if pre_best and g < pre_best[0]), default=None)
        # per-worker own-best drops in the last quarter / last half (seeded arms)
        drops_q4 = sum(1 for _, r, _ in seeded for t, g, d, mv, rs in r["series"] if t >= 0.75 * dur)
        drops_h2 = sum(1 for _, r, _ in seeded for t, g, d, mv, rs in r["series"] if t >= 0.5 * dur)
        # merged own-best value at a time (start = best seed gates at <= cap over seeded workers)
        start_best = min((r_["start_gates"] for r_ in worker_rows if r_["run"] == tag and r_["map"] == target and r_["start_gates"] is not None), default=None)

        def best_at(tt):
            v = start_best
            for t, g in own:
                if t <= tt and (v is None or g < v):
                    v = g
            return v
        gates_h2 = (best_at(0.5 * dur) - best_at(dur)) if own and start_best is not None else 0
        gates_q4 = (best_at(0.75 * dur) - best_at(dur)) if own and start_best is not None else 0
        gates_h1 = (start_best - best_at(0.5 * dur)) if own and start_best is not None else 0
        tf = [r_["t_first_imp_s"] for r_ in worker_rows if r_["run"] == tag and r_["map"] == target and r_["arm"] != "fresh" and r_["t_first_imp_s"] is not None]
        tg = [r_["t_first_gain_s"] for r_ in worker_rows if r_["run"] == tag and r_["map"] == target and r_["t_first_gain_s"] is not None]
        itr = [r_["it_per_s"] for r_ in worker_rows if r_["run"] == tag and r_["map"] == target and r_["it_per_s"]]
        fresh = [(w, r) for w, r, arm in wk if arm == "fresh"]
        fresh_best = None; fresh_reach = None
        if fresh:
            fb = [x for x in fresh[0][1]["frontier"] if x[1] <= cap]
            fresh_best = f"{min(fb)[0]}@{min(fb)[1]}" if fb else "-"
            fresh_reach = next((round(t) for t, g, d, mv, rs in fresh[0][1]["series"] if pre_best and g <= pre_best[0]), None)
        wbests = "; ".join(f"{arm}:{r_['best_le_cap']}" for r_ in worker_rows if r_["run"] == tag and r_["map"] == target for arm in [r_["arm"]])
        frac_last = (t_last_own / dur) if t_last_own is not None else None
        if frac_last is None:
            klass = "no drop"
        elif frac_last >= 0.75:
            klass = "still improving"
        elif frac_last >= 0.5:
            klass = "slowing"
        else:
            klass = "plateaued"
        with open(os.path.join(series_dir, f"{tag}-{target}-merged.txt"), "w") as f:
            f.write(f"# {tag} {target} cap {cap} merged own-best at <= cap over seeded workers; repo best {pre_best}\n")
            for t, g in own:
                f.write(f"{t:8.1f} {g:5d}\n")
        trial_rows.append(dict(
            run=tag, map=target, cls=cls, size=size, n_in=int(p["n_in"]), cap=cap, workers=len(ws), worker_h=len(ws) * dur / 3600.0,
            duration_s=dur, seeds="; ".join(sorted(seeds_desc)),
            repo_best=f"{pre_best[0]}@{pre_best[1]}" if pre_best else "-", repo_best_g=pre_best[0] if pre_best else None,
            nist=f"{nist_best[0]}@{nist_best[1]}" if nist_best else "-", nist_g=nist_best[0] if nist_best else None,
            result_le_cap=f"{res_le[0]}@{res_le[1]}" if res_le else "-", result_g=res_le[0] if res_le else None,
            result_arm="/".join(sorted(set(res_arm))), worker_bests=wbests,
            gain_cap=gain_cap, gain_cap_rel=round(gain_cap / pre_best[0], 4) if gain_cap is not None else None,
            gain_any=gain_any, gain_any_pt=gain_any_pt,
            seed_slack=slack, res_depth=res_depth, nearest_prior_depth_dist=near, band_populated=int(near is not None and near <= 1),
            pre_gap_vs_nist=None if pre_gap is None else round(pre_gap, 4), post_gap_vs_nist=None if post_gap is None else round(post_gap, 4),
            any_best_pre=f"{any_best[0]}@{any_best[1]}" if any_best else "-", depth_drift=drift,
            pre_depths=" ".join(f"{g}@{d}" for g, d in sorted(pre_pts, key=lambda x: x[1])),
            t_first_imp_s=min(tf) if tf else None, t_first_gain_s=min(tg) if tg else None,
            t_last_own_drop_s=None if t_last_own is None else round(t_last_own), t_last_gain_s=None if t_last_gain is None else round(t_last_gain),
            frac_last_drop=None if frac_last is None else round(frac_last, 2), klass=klass,
            start_best=start_best, drops_q4=drops_q4, drops_h2=drops_h2, own_gain_h1=gates_h1, own_gain_h2=gates_h2, own_gain_q4=gates_q4,
            gain_q1=q[0], gain_q2=q[1], gain_q3=q[2], gain_q4=q[3],
            gain_q1_all=qa[0], gain_q2_all=qa[1], gain_q3_all=qa[2], gain_q4_all=qa[3],
            it_per_s=round(sum(itr) / len(itr)) if itr else None,
            fresh_best=fresh_best, fresh_reach_repo_s=fresh_reach, **ph))

with open(os.path.join(OUT, "trials.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(trial_rows[0].keys()))
    w.writeheader()
    for r in trial_rows:
        w.writerow(r)
with open(os.path.join(OUT, "workers.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(worker_rows[0].keys()))
    w.writeheader()
    for r in worker_rows:
        w.writerow(r)
print(len(trial_rows), "trials,", len(worker_rows), "workers")
for r in trial_rows:
    print(f"{r['run']:4s} {r['map']:27s} {r['cls']} cap{r['cap']:3d} [{r['seeds']}] {r['repo_best']:7s}->{r['result_le_cap']:7s}({r['result_arm']}) "
          f"g {r['gain_cap']!s:3s} any {r['gain_any']!s:3s} slk {r['seed_slack']!s:2s} nr {r['nearest_prior_depth_dist']!s:2s} "
          f"wh cap/ge/tot {r['wh_cap']:.1f}/{r['wh_ge']:.1f}/{r['wh_total']:.1f} "
          f"t1 {r['t_first_imp_s']} tg {r['t_first_gain_s']} tl {r['t_last_own_drop_s']} ({r['frac_last_drop']}) {r['klass']:15s} "
          f"q {r['gain_q1']}/{r['gain_q2']}/{r['gain_q3']}/{r['gain_q4']} own h1/h2/q4 {r['own_gain_h1']}/{r['own_gain_h2']}/{r['own_gain_q4']} dq4 {r['drops_q4']} it/s {r['it_per_s']} fresh {r['fresh_best']} @{r['fresh_reach_repo_s']}")
