#!/bin/bash
# Overhead check 2: the same pair for 5 min with replayable scheduling (scheduler.cost = work),
# so both arms follow the SAME trajectory from the same rng seed and the steps-per-CPU-second
# ratio measures the logging alone (machine noise aside).  Writes runs-w/T0, runs-w/T1.
set -u
T="$HOME/xs-campaigns/2026-11-07-sprint/translog"
cd "$T" || exit 1
rm -rf "$T/runs-w"
mkdir -p "$T/runs-w"
for arm in T0 T1; do
  sed -e 's/^duration = "20m"/duration = "5m"/' -e "s/^name = \"translog-$arm\"/name = \"translog-$arm-work\"/" \
      -e 's/^"restart.w_best" = 0.0/"restart.w_best" = 0.0\n"scheduler.cost" = "work"/' "$T/$arm.toml" > "$T/${arm}w.toml"
  nice -n 8 python3 "$T/xorflux-translog/xorflux" run "$T/${arm}w.toml" --out "$T/runs-w/$arm" \
      --set campaign.allow_oversubscription=true > "$T/${arm}w.run.log" 2>&1 &
done
wait
for arm in T0 T1; do
  python3 - "$T/runs-w/$arm/workers/free-00" <<'EOF'
import json, sys
w = sys.argv[1]
d = json.load(open(w + "/status.json"))
stop = None
for line in open(w + "/events.jsonl"):
    if '"ev":"stop"' in line:
        stop = json.loads(line)
tot = stop["totals"]
print(w.split("/")[-3], "steps", d["steps"], "accepted", d["accepted"], "t", round(d["t"], 1),
      "cpu_s", round(stop["cpu_s"], 2), "steps/cpu_s", round(d["steps"] / stop["cpu_s"], 2),
      "work", d["engine"]["work"], "cur", d["engine"]["cur"],
      "remove1", tot.get("walk.remove1", {}).get("proposals"), tot.get("walk.remove1", {}).get("accepted"))
EOF
done
touch "$T/DONE_W"
