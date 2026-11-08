#!/bin/bash
# Patch the copy, byte-compile it, run the engine-loop unit tests on it, then a 75 s smoke run
# of the T1 configuration (S1.toml) and print the first rows of its transition log.
set -u
T="$HOME/xs-campaigns/2026-11-07-sprint/translog"
cd "$T" || exit 1
true
python3 make_tomls.py || exit 1
python3 -m compileall -q xorflux-translog/xorflux > /dev/null || { echo COMPILE FAILED; exit 1; }
echo "---- unit tests (engine loop, worker, plan) on the copy"
( cd xorflux-translog && timeout 600 python3 -m unittest xorflux.tests.test_engine_loop xorflux.tests.test_campaign_worker xorflux.tests.test_campaign_plan 2>&1 | tail -5 )
echo "---- smoke run S1 (75 s)"
rm -rf "$T/runs-smoke"
nice -n 8 python3 "$T/xorflux-translog/xorflux" run "$T/S1.toml" --out "$T/runs-smoke" --set campaign.allow_oversubscription=true > "$T/S1.run.log" 2>&1
echo "exit $?"
tail -5 "$T/S1.run.log"
W="$T/runs-smoke/workers/free-00"
ls "$W"
echo "---- translog rows: $(wc -l < "$W/translog.jsonl")"
head -c 600 "$W/translog.jsonl"; echo
grep '"k":"close"' "$W/translog.jsonl"
grep -o '"ev":"stop".*' "$W/events.jsonl" | cut -c1-300
python3 - "$W/status.json" <<'EOF'
import json, sys
d = json.load(open(sys.argv[1]))
print("steps", d["steps"], "t", round(d["t"], 1), "steps/s", round(d["steps_per_second"], 1), "best", d["best"] and d["best"]["gates"], "engine", d["engine"])
EOF
cat "$W/error.json" 2>/dev/null | head -20
