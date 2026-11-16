#!/usr/bin/env python3
"""Collect results/*/summary.json into abc_results.json and a Markdown table.
Usage: collect.py EXT_DIR OUT_JSON OUT_TABLE_MD [CIRCUIT_DIR]
"""
import glob
import json
import os
import shutil
import statistics
import sys

ext, out_json, out_md = sys.argv[1:4]
circ_dir = sys.argv[4] if len(sys.argv) > 4 else None
runs = []
for p in sorted(glob.glob(os.path.join(ext, "results", "*", "summary.json"))):
    d = json.load(open(p))
    tag, lib, flow, s = os.path.basename(os.path.dirname(p)).split("__")
    b = d["best"]
    m = b.get("metrics", {})
    runs.append({
        "target": tag, "model": lib, "flow": flow, "seed": int(s[1:]),
        "budget_s": d["budget"], "chunk_s": d["chunk"], "steps": d["steps"],
        "nonzero_rc_steps": d.get("nonzero_rc", []),
        "G": b.get("G"), "counts": m.get("counts"), "GD": m.get("GD"), "AD": m.get("AD"),
        "A_nonlinear": m.get("A"), "XX": m.get("XX"), "cost": m.get("cost"),
        "time_to_best_s": b.get("t"), "best_step": b.get("step"), "best_mapper": b.get("mapper"),
        "total_time_s": d["total_time"], "peak_rss_kb": d["peak_rss_kb"],
        "converter_notes": b.get("notes", []),
        "ncff": os.path.relpath(b["ncff"], ext) if b.get("ncff") else None,
    })

groups = {}
for r in runs:
    groups.setdefault((r["target"], r["model"]), []).append(r)

lines = ["| target | model | flow | seeds | best G per seed | best G | counts (best) | GD | AD | nonlin | t to best (s) | total (s) | peak RSS (MB) |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
best_overall = {}
for (t, lib), rs in groups.items():
    for flow in ("classic", "deepsyn", "eslim"):
        fr = sorted([r for r in rs if r["flow"] == flow], key=lambda r: r["seed"])
        if not fr:
            continue
        gs = [r["G"] for r in fr]
        b = min(fr, key=lambda r: (r["G"], r["time_to_best_s"]))
        cnt = " ".join(f"{k}{v}" for k, v in sorted(b["counts"].items()))
        lines.append(f"| {t} | {lib} | {flow} | {','.join(str(r['seed']) for r in fr)} | "
                     f"{' '.join(map(str, gs))} | **{b['G']}** | {cnt} | {b['GD']} | {b['AD']} | "
                     f"{b['A_nonlinear']} | {b['time_to_best_s']} | "
                     f"{max(r['total_time_s'] for r in fr)} | {max(r['peak_rss_kb'] for r in fr)/1024:.0f} |")
    b = min(rs, key=lambda r: (r["G"], r["time_to_best_s"]))
    best_overall[f"{t}/{lib}"] = {k: b[k] for k in ("G", "flow", "seed", "counts", "GD", "AD",
                                                     "A_nonlinear", "time_to_best_s", "ncff")}
    if circ_dir:
        os.makedirs(circ_dir, exist_ok=True)
        dst = os.path.join(circ_dir, f"abc-{t}-{lib}-g{b['G']}.circ.txt")
        shutil.copy(os.path.join(ext, b["ncff"]), dst)
        best_overall[f"{t}/{lib}"]["file"] = os.path.basename(dst)

json.dump({"best": best_overall, "runs": runs}, open(out_json, "w", encoding="utf-8", newline="\n"),
          indent=1)
open(out_md, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
print("\n".join(lines))
print(json.dumps(best_overall, indent=1))
