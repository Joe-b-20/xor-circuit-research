#!/usr/bin/env python3
"""Markdown tables for REPORT.md from trials.csv / workers.csv -> table.md"""
import csv, os
OUT = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/xmapsep")
T = list(csv.DictReader(open(os.path.join(OUT, "trials.csv"))))
W = list(csv.DictReader(open(os.path.join(OUT, "workers.csv"))))
f = open(os.path.join(OUT, "table.md"), "w")


def s(v):
    return "-" if v in ("", None, "None") else str(v)


def mins(v):
    try:
        return f"{float(v)/60:.0f}"
    except Exception:
        return "-"


f.write("| # | run | map | matrix | cap | trial wh | started from | repo best <=cap | NIST | result <=cap (arm) | gain@cap | gain any (point) | slack | nearest prior depth | prior wh: cap / cap>= / total | 1st imp (min) | 1st gain (min) | last own drop (min, frac) | class |\n")
f.write("|---|---|---|---|---:|---:|---|---|---|---|---:|---|---:|---:|---|---:|---:|---|---|\n")
for i, r in enumerate(sorted(T, key=lambda r: (r["cls"] != "8x8", ["x1a", "x1b", "pt1", "pt2", "sw1", "sw2"].index(r["run"]))), 1):
    starts = "; ".join(sorted({w["start"] for w in W if w["run"] == r["run"] and w["map"] == r["map"]}))
    f.write(f"| {i} | {r['run']} | {r['map']} | {r['size']} | {r['cap']} | {float(r['worker_h']):.0f} | {starts} | {r['repo_best']} | {r['nist']} | "
            f"{r['result_le_cap']} ({r['result_arm']}) | {r['gain_cap']} | {s(r['gain_any'])} ({s(r['gain_any_pt'])}) | {r['seed_slack']} | {r['nearest_prior_depth_dist']} | "
            f"{float(r['wh_cap']):.0f} / {float(r['wh_ge']):.0f} / {float(r['wh_total']):.0f} | {mins(r['t_first_imp_s'])} | {mins(r['t_first_gain_s'])} | "
            f"{mins(r['t_last_own_drop_s'])} ({s(r['frac_last_drop'])}) | {r['klass']} |\n")
f.write("\n\nPer-worker table (what each worker started from and reached; 'drops' = times its own best at <= cap fell below its start):\n\n")
f.write("| run | worker | start | best <=cap | best any | drops | restarts | first imp (s) | last drop (s) | it/s | sources of improvements |\n|---|---|---|---|---|---:|---:|---:|---:|---:|---|\n")
for w in W:
    f.write(f"| {w['run']} | {w['worker']} | {w['start']} | {w['best_le_cap']} | {w['best_any']} | {w['n_drops_le_cap']} | {w['restarts']} | {s(w['t_first_imp_s'])} | {s(w['t_last_drop_s'])} | {w['it_per_s']} | {w['sources']} |\n")
f.close()
print(open(os.path.join(OUT, "table.md")).read())
