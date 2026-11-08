#!/bin/bash
# Smoke run only (the copy is already patched): 75 s of the T1 configuration.
# core/target.py derives the repo root two levels above the package, so translog/circuits must
# point at the repository's circuits catalogue (as v10-proto did).
set -u
T="$HOME/xs-campaigns/2026-11-07-sprint/translog"
cd "$T" || exit 1
[ -e "$T/circuits" ] || ln -s "$HOME/xor-circuit-research/circuits" "$T/circuits"
rm -rf "$T/runs-smoke"
nice -n 8 python3 "$T/xorflux-translog/xorflux" run "$T/S1.toml" --out "$T/runs-smoke" --set campaign.allow_oversubscription=true > "$T/S1.run.log" 2>&1
echo "exit $?"
tail -4 "$T/S1.run.log"
W="$T/runs-smoke/workers/free-00"
ls "$W"
echo "---- translog rows: $(wc -l < "$W/translog.jsonl")"
head -c 700 "$W/translog.jsonl"; echo
echo "---- kinds"
grep -o '"k":"[a-z]*"' "$W/translog.jsonl" | sort | uniq -c
grep '"k":"close"' "$W/translog.jsonl"
grep -o '"ev":"stop".*' "$W/events.jsonl" | cut -c1-200
grep -o '"translog":{[^}]*}' "$W/events.jsonl" | tail -1
python3 - "$W/status.json" <<'EOF'
import json, sys
d = json.load(open(sys.argv[1]))
print("steps", d["steps"], "t", round(d["t"], 1), "steps/s", round(d["steps_per_second"], 1), "best", d["best"] and d["best"]["gates"], "engine", d["engine"])
EOF
cat "$W/error.json" 2>/dev/null | head -20
ls -la "$W/translog.jsonl"
