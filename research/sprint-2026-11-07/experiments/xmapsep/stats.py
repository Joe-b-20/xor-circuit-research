#!/usr/bin/env python3
"""xmapsep stats: rank correlations, 2x2 tables, within-run classification, repeats. Reads trials.csv,
workers.csv; writes stats.txt."""
import csv, os, sys, math, collections
import numpy as np
from scipy import stats

OUT = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/xmapsep")
T = list(csv.DictReader(open(os.path.join(OUT, "trials.csv"))))
W = list(csv.DictReader(open(os.path.join(OUT, "workers.csv"))))
out = open(os.path.join(OUT, "stats.txt"), "w")


def P(*a):
    s = " ".join(str(x) for x in a)
    print(s); out.write(s + "\n")


def num(r, k):
    v = r.get(k, "")
    try:
        return float(v)
    except Exception:
        return float("nan")


for r in T:
    r["gain"] = max(0.0, num(r, "gain_cap"))      # skop15-8x8-gf16 x1a: -5 (NIST-seeded arm never reached our 146) -> 0
    r["gain_raw"] = num(r, "gain_cap")
    r["g1"] = int(r["gain"] >= 1); r["g3"] = int(r["gain"] >= 3)
    r["is8"] = int(r["cls"] == "8x8")
    for k in ("wh_cap", "wh_cap1", "wh_ge", "wh_total", "seed_slack", "nearest_prior_depth_dist", "n_in", "repo_best_g",
              "it_per_s", "worker_h", "gain_cap_rel", "t_first_gain_s", "t_last_own_drop_s", "frac_last_drop", "own_gain_h1",
              "own_gain_h2", "own_gain_q4", "duration_s", "band_populated", "pre_gap_vs_nist", "post_gap_vs_nist", "depth_drift"):
        r[k] = num(r, k)
    r["abs_drift"] = abs(r["depth_drift"])
    r["wh_cap_it"] = r["wh_cap"] * r["it_per_s"]            # prior iterations at the cap (proxy: trial it/s)
    r["wh_total_it"] = r["wh_total"] * r["it_per_s"]
    r["wh_total_it_per_gate"] = r["wh_total_it"] / r["repo_best_g"]
    r["gain_rel"] = r["gain"] / r["repo_best_g"]
    r["log_wh_total"] = math.log10(r["wh_total"] + 0.1)

ALL = T; B8 = [r for r in T if r["is8"]]; B4 = [r for r in T if not r["is8"]]
P("=" * 100)
P("SPEARMAN rank correlations of gain at the cap (gates, floored at 0) with candidate predictors")
P("  n = 27 all trials; n = 20 8x8-matrix maps; n = 7 4x4 maps.  [measured: trials.csv]")
P("=" * 100)
preds = [("wh_cap", "(i) prior worker-h at exactly this cap"), ("wh_cap1", "(i) prior worker-h at cap +-1"),
         ("wh_ge", "(i) prior worker-h with cap >= this cap or uncapped"), ("wh_total", "(i) prior worker-h on the map, any cap"),
         ("log_wh_total", "(i) log10 prior worker-h on map"),
         ("wh_total_it", "(i') prior worker-iterations on map (hours x trial it/s)"),
         ("wh_total_it_per_gate", "(i') prior iterations per gate of the seed"),
         ("worker_h", "trial compute (worker-h in this trial)"),
         ("seed_slack", "(ii) cap - depth of our best seed (0 = seed sits at the cap)"),
         ("nearest_prior_depth_dist", "(ii) |depth of result - nearest prior circuit depth|"),
         ("n_in", "size: inputs"), ("repo_best_g", "size: gates of our best at <= cap"),
         ("it_per_s", "iteration rate (inverse size proxy)"),
         ("pre_gap_vs_nist", "(iii) how far below NIST at the cap our seed already was, (NIST-ours)/NIST"),
         ("depth_drift", "depth of our pre-trial any-depth best minus the cap (>0: earlier search drifted deeper)"),
         ("abs_drift", "|depth drift|")]
P(f"{'predictor':28s} {'all rho':>8s} {'p':>7s}   {'8x8 rho':>8s} {'p':>7s}   {'4x4 rho':>8s} {'p':>7s}   note")
for k, note in preds:
    row = f"{k:28s}"
    for sub in (ALL, B8, B4):
        x = [r[k] for r in sub]; y = [r["gain"] for r in sub]
        if len(set(x)) < 2 or len(set(y)) < 2:
            row += f" {'const':>8s} {'':>7s}  "
        else:
            rho, p = stats.spearmanr(x, y)
            row += f" {rho:8.2f} {p:7.3f}  "
    P(row + "  " + note)
P()
P("Same, outcome = relative gain (gates gained / gates of our best at <= cap):")
P(f"{'predictor':28s} {'all rho':>8s} {'p':>7s}   {'8x8 rho':>8s} {'p':>7s}")
for k, note in preds:
    row = f"{k:28s}"
    for sub in (ALL, B8):
        x = [r[k] for r in sub]; y = [r["gain_rel"] for r in sub]
        if len(set(x)) < 2:
            row += f" {'const':>8s} {'':>7s}  "
        else:
            rho, p = stats.spearmanr(x, y)
            row += f" {rho:8.2f} {p:7.3f}  "
    P(row)
P()


def partial(sub, y, x, zs):
    """Spearman partial: rank-transform, regress out zs, correlate residuals."""
    def rk(v):
        return stats.rankdata(v)
    Y = rk([r[y] for r in sub]); X = rk([r[x] for r in sub])
    Z = np.column_stack([rk([r[z] for r in sub]) for z in zs] + [np.ones(len(sub))])
    def resid(v):
        beta, *_ = np.linalg.lstsq(Z, v, rcond=None)
        return v - Z @ beta
    rho, p = stats.pearsonr(resid(Y), resid(X))
    return rho, p


P("PARTIAL rank correlations (residual ranks), gain vs size (n_in) and vs class controlling for (i)/(ii):")
for zs in (["wh_cap"], ["wh_total"], ["seed_slack"], ["wh_cap", "seed_slack"], ["wh_total", "seed_slack"], ["wh_total_it_per_gate"],
           ["wh_total_it_per_gate", "seed_slack"]):
    rho, p = partial(ALL, "gain", "n_in", zs)
    rho2, p2 = partial(ALL, "gain", "is8", zs)
    P(f"  control {str(zs):40s} gain~n_in rho {rho:+.2f} p {p:.3f};  gain~is8x8 rho {rho2:+.2f} p {p2:.3f}")
P("  and the reverse: gain vs prior hours controlling for size")
for x in ("wh_cap", "wh_total", "wh_total_it_per_gate", "seed_slack"):
    rho, p = partial(ALL, "gain", x, ["n_in"])
    rho8, p8 = partial(B8, "gain", x, ["n_in"]) if len(set(r[x] for r in B8)) > 1 else (float("nan"), float("nan"))
    P(f"  gain~{x:22s} | n_in : all rho {rho:+.2f} p {p:.3f};  8x8 rho {rho8:+.2f} p {p8:.3f}")
P()

P("=" * 100)
P("2x2 TABLES (Fisher exact, two-sided)  [measured: trials.csv]")
P("=" * 100)


def table(sub, a, alab, b, blab, title):
    n11 = sum(1 for r in sub if a(r) and b(r)); n10 = sum(1 for r in sub if a(r) and not b(r))
    n01 = sum(1 for r in sub if not a(r) and b(r)); n00 = sum(1 for r in sub if not a(r) and not b(r))
    odds, p = stats.fisher_exact([[n11, n10], [n01, n00]])
    P(f"{title}")
    P(f"   {'':24s} {blab[0]:>12s} {blab[1]:>12s}")
    P(f"   {alab[0]:24s} {n11:12d} {n10:12d}")
    P(f"   {alab[1]:24s} {n01:12d} {n00:12d}      Fisher p = {p:.3f}")


table(ALL, lambda r: r["is8"], ("8x8 maps", "4x4 maps"), lambda r: r["g1"], ("gain >= 1", "no gain"), "class x gain>=1 (all 27)")
table(ALL, lambda r: r["is8"], ("8x8 maps", "4x4 maps"), lambda r: r["g3"], ("gain >= 3", "gain <= 2"), "class x gain>=3 (all 27)")
table(ALL, lambda r: r["wh_cap"] > 0, ("prior h at cap > 0", "prior h at cap = 0"), lambda r: r["g1"], ("gain >= 1", "no gain"), "(i) prior hours at exactly the cap x gain>=1 (all 27)")
table(B8, lambda r: r["wh_cap"] > 0, ("prior h at cap > 0", "prior h at cap = 0"), lambda r: r["g3"], ("gain >= 3", "gain <= 2"), "(i) prior hours at the cap x gain>=3 (8x8 only)")
table(B8, lambda r: r["wh_total"] > 2.5, ("prior h on map > 2.5", "prior h on map <= 2.5"), lambda r: r["g3"], ("gain >= 3", "gain <= 2"), "(i) prior hours on the map (any cap) x gain>=3 (8x8 only; 2 h = the batch protocol)")
table(B8, lambda r: r["seed_slack"] > 0, ("seed below cap (slack>0)", "seed at cap (slack=0)"), lambda r: r["g3"], ("gain >= 3", "gain <= 2"), "(ii) seed depth slack x gain>=3 (8x8 only)")
table(B8, lambda r: r["seed_slack"] > 0, ("seed below cap (slack>0)", "seed at cap (slack=0)"), lambda r: r["g1"], ("gain >= 1", "no gain"), "(ii) seed depth slack x gain>=1 (8x8 only)")
table(ALL, lambda r: r["seed_slack"] > 0, ("seed below cap (slack>0)", "seed at cap (slack=0)"), lambda r: r["g1"], ("gain >= 1", "no gain"), "(ii) seed depth slack x gain>=1 (all 27)")
table(ALL, lambda r: r["band_populated"] == 0, ("result band empty before", "result band had a circuit"), lambda r: r["g3"], ("gain >= 3", "gain <= 2"), "(ii) result depth band (+-1) empty before the trial x gain>=3 (all 27)")
P()
P("Gap below NIST at the cap, before and after the trial, by class [measured: trials.csv]:")
for sub, lab in ((B8, "8x8"), (B4, "4x4")):
    pre_ = sorted(r["pre_gap_vs_nist"] for r in sub); post_ = sorted(r["post_gap_vs_nist"] for r in sub)
    P(f"  {lab}: before median {100*np.median(pre_):.1f}% [{100*pre_[0]:.1f}-{100*pre_[-1]:.1f}]; after median {100*np.median(post_):.1f}% [{100*post_[0]:.1f}-{100*post_[-1]:.1f}]")
P("  per trial (8x8), sorted by gain: " + "; ".join(f"{r['map']}:{100*r['pre_gap_vs_nist']:.1f}->{100*r['post_gap_vs_nist']:.1f}%" for r in sorted(B8, key=lambda r: -r["gain"])))
P("  per trial (4x4): " + "; ".join(f"{r['map']}:{100*r['pre_gap_vs_nist']:.1f}->{100*r['post_gap_vs_nist']:.1f}%" for r in B4))
P("  Spearman gain_rel vs pre_gap (8x8):", stats.spearmanr([r["pre_gap_vs_nist"] for r in B8], [r["gain_rel"] for r in B8]))
P("  Spearman post_gap vs pre_gap (8x8):", stats.spearmanr([r["pre_gap_vs_nist"] for r in B8], [r["post_gap_vs_nist"] for r in B8]))
P()
P("Mann-Whitney U, gain 8x8 vs 4x4:", stats.mannwhitneyu([r["gain"] for r in B8], [r["gain"] for r in B4], alternative="two-sided"))
P("Mann-Whitney U, relative gain 8x8 vs 4x4:", stats.mannwhitneyu([r["gain_rel"] for r in B8], [r["gain_rel"] for r in B4], alternative="two-sided"))
P()
P("Prior search received, by class (median [min-max]) [measured: prior_wh.csv via trials.csv]:")
for k in ("wh_cap", "wh_cap1", "wh_ge", "wh_total", "wh_total_it", "wh_total_it_per_gate", "it_per_s", "repo_best_g"):
    v8 = sorted(r[k] for r in B8); v4 = sorted(r[k] for r in B4)
    P(f"  {k:22s} 8x8: {np.median(v8):10.1f} [{v8[0]:.1f}-{v8[-1]:.1f}]   4x4: {np.median(v4):10.1f} [{v4[0]:.1f}-{v4[-1]:.1f}]")
P()

P("=" * 100)
P("WITHIN-RUN: last drop of the (seeded) workers' own best at <= cap, as a fraction of the run; gains by half")
P("  klass: still improving = last drop in the final quarter; slowing = in the third quarter; plateaued = first half")
P("=" * 100)
P(f"{'run':4s} {'map':27s} {'cls':3s} {'gain':>4s} {'t_last/dur':>10s} {'klass':16s} {'own h1':>6s} {'own h2':>6s} {'own q4':>6s} {'drops q4':>8s} {'start':>5s} -> {'end':>5s}")
for r in sorted(T, key=lambda r: (-r["is8"], -r["gain"])):
    P(f"{r['run']:4s} {r['map']:27s} {r['cls']:3s} {int(r['gain_raw']):4d} {r['frac_last_drop']:10.2f} {r['klass']:16s} {int(r['own_gain_h1']):6d} {int(r['own_gain_h2']):6d} {int(r['own_gain_q4']):6d} {r['drops_q4']:>8s} {r['start_best']:>5s} -> {r['result_le_cap']:>7s}")
P()
cnt = collections.Counter((r["cls"], r["klass"]) for r in T)
for c in ("8x8", "4x4"):
    P(f"  {c}: " + ", ".join(f"{k} {cnt[(c, k)]}" for k in ("still improving", "slowing", "plateaued", "no drop")))
P("  among 8x8 trials with gain >= 3: " + ", ".join(f"{k} {sum(1 for r in B8 if r['g3'] and r['klass'] == k)}" for k in ("still improving", "slowing", "plateaued")))
P("  among 8x8 trials with gain <= 2: " + ", ".join(f"{k} {sum(1 for r in B8 if not r['g3'] and r['klass'] == k)}" for k in ("still improving", "slowing", "plateaued")))
P("  Spearman gain vs frac_last_drop (all):", stats.spearmanr([r["gain"] for r in T if not math.isnan(r["frac_last_drop"])], [r["frac_last_drop"] for r in T if not math.isnan(r["frac_last_drop"])]))
P("  Second-half share of the own gain, 8x8 trials with own gain > 0: " + ", ".join(
    f"{r['map'].split('-')[0]}:{int(r['own_gain_h2'])}/{int(r['own_gain_h1'] + r['own_gain_h2'])}" for r in B8 if r["own_gain_h1"] + r["own_gain_h2"] > 0))
tot_h1 = sum(r["own_gain_h1"] for r in B8); tot_h2 = sum(r["own_gain_h2"] for r in B8); tot_q4 = sum(r["own_gain_q4"] for r in B8)
P(f"  8x8 totals: first half {int(tot_h1)} gates, second half {int(tot_h2)}, final quarter {int(tot_q4)} (own-best series, seeded workers)")
P()
P("pt trials (2 h per worker): gates gained from the start seed in hour 1 vs hour 2 (merged own-best series):")
for r in T:
    if r["run"].startswith("pt"):
        P(f"  {r['run']} {r['map']:27s} hour1 {int(r['own_gain_h1'])}  hour2 {int(r['own_gain_h2'])}  last drop at {r['t_last_own_drop_s']} s of {int(r['duration_s'])}")
P()

P("=" * 100)
P("REPEATS AND SEED COMPARISONS  [measured: workers.csv]")
P("=" * 100)
P("Per-worker results (pt trials have two workers per map: one started from our best, one from NIST's):")
for w in W:
    if w["run"].startswith("pt") or w["run"].startswith("x1"):
        P(f"  {w['run']} {w['worker']:34s} start {w['start']:14s} -> {w['best_le_cap']:8s} drops {w['n_drops_le_cap']:>3s} first imp {w['t_first_imp_s']:>5s} s, last drop {w['t_last_drop_s']:>5s} s, restarts {w['restarts']}")
P()
P("Same map, same cap, independent runs (natural repeats):")
rep = [("klsw17-m-8x8-gf256-inv cap 12 from NIST 368@12", ["x1a:klsw17-m-8x8-gf256-inv-nist-00", "pt1:klsw17-m-8x8-gf256-inv-01"]),
       ("klsw17-m-8x8-gf256-inv cap 12 from ours 346@12", ["pt1:klsw17-m-8x8-gf256-inv-00"]),
       ("khazad cap 18 from ours 345@15", ["pt2:khazad-00", "sw1:khazad-00"]),
       ("khazad cap 18 from NIST 366@18", ["pt2:khazad-01"]),
       ("fox-mu8 cap 14 from ours 505@11", ["pt2:fox-mu8-00", "sw1:fox-mu8-00"]),
       ("fox-mu8 cap 14 from NIST 540@14", ["pt2:fox-mu8-01"]),
       ("skop15-8x8-gf16 cap 19 from NIST 170@19", ["x1a:skop15-8x8-gf16-nist-00", "pt1:skop15-8x8-gf16-01"]),
       ("grostl from NIST 410@12 (cap 12 x1a; cap 16 sw1 had ours 350@16)", ["x1a:grostl-nist-00", "sw1:grostl-00"])]
idx = {f"{w['run']}:{w['worker']}": w for w in W}
for title, keys in rep:
    P(f"  {title}:")
    for k in keys:
        w = idx[k]
        P(f"     {k:40s} {w['wall_s']:>5s} s -> {w['best_le_cap']:8s} (last drop {w['t_last_drop_s']} s)")
out.close()
