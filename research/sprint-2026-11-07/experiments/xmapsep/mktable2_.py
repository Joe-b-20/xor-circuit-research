#!/usr/bin/env python3
import csv, os
OUT = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/xmapsep")
T = list(csv.DictReader(open(os.path.join(OUT, "trials.csv"))))
with open(os.path.join(OUT, "table2.md"), "w") as f:
    f.write("| run | map | cls | cap | our pre-trial best, any depth | depth drift (that depth - cap) | gap below NIST at cap: before | after | own gain h1 / h2 / last quarter | last own drop (frac of run) | class |\n|---|---|---|---:|---|---:|---:|---:|---|---:|---|\n")
    for r in sorted(T, key=lambda r: (r["cls"] != "8x8", -float(r["gain_cap"]))):
        f.write("| %s | %s | %s | %s | %s | %s | %.1f%% | %.1f%% | %s / %s / %s | %s | %s |\n" % (
            r["run"], r["map"], r["cls"], r["cap"], r["any_best_pre"], r["depth_drift"], 100 * float(r["pre_gap_vs_nist"]),
            100 * float(r["post_gap_vs_nist"]), r["own_gain_h1"], r["own_gain_h2"], r["own_gain_q4"], r["frac_last_drop"] or "-", r["klass"]))
print(open(os.path.join(OUT, "table2.md")).read())
