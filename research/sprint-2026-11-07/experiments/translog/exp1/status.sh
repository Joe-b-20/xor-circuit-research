#!/bin/bash
# Progress of exp1: driver log, per-worker phase / steps / current point / translog rows, errors.
E="$HOME/xs-campaigns/2026-11-07-sprint/translog/exp1"
date -u +%H:%M:%SZ
uptime
cat "$E/driver.log"
python3 - "$E" <<'EOF'
import json, os, sys, glob
E = sys.argv[1]
for w in sorted(glob.glob(E + "/runs/E1/workers/*")):
    try:
        d = json.load(open(w + "/status.json"))
    except Exception as exc:
        print(os.path.basename(w), "no status:", exc); continue
    tl = w + "/translog.jsonl"
    rows = sum(1 for _ in open(tl)) if os.path.exists(tl) else 0
    eng = d.get("engine") or {}
    print(f"{os.path.basename(w)} {d['phase']:8s} steps {d['steps']:>9} t {d['t']:7.0f} "
          f"{d['steps_per_second']:7.1f}/s cur {eng.get('cur')} best {eng.get('worker_best')} "
          f"chain {eng.get('chain')} translog rows {rows}")
    if os.path.exists(w + "/error.json"):
        print("  ERROR:", open(w + "/error.json").read()[:400])
s = E + "/samples/samples.jsonl"
print("sampler records:", sum(1 for _ in open(s)) if os.path.exists(s) else 0)
EOF
