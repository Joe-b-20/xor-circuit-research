#!/bin/bash
# Parallel scoped-SAT campaign 2.  usage: bash batch2.sh [N]   (default N = 12 solver processes)
# Each shard: nice -n 5, its own results_batch2.shard<i>.jsonl; merged by batch_summary.py batch2.
# Plan only (no solver): bash batch2.sh --plan [N]
# Stop cleanly: touch ~/xs-campaigns/2026-11-07-sprint/sat/STOP.  Find: sat/FOUND_87.
cd ~/xs-campaigns/2026-11-07-sprint/sat || exit 1
if [ "$1" = "--plan" ]; then
  N=${2:-12}
  [ -f batch2_circuits.json ] || nice -n 5 python3 batch2_driver.py --prepare
  exec nice -n 5 python3 batch2_driver.py --plan --nshards "$N"
fi
N=${1:-12}
[ -f batch2_circuits.json ] || nice -n 5 python3 batch2_driver.py --prepare >> batch2.out 2>&1
pids=""
for ((i=0; i<N; i++)); do
  nice -n 5 python3 batch2_driver.py --shard "$i" --nshards "$N" >> "batch2.shard$i.out" 2>&1 &
  pids="$pids $!"
done
echo "$(date -u +%FT%TZ) batch2 started N=$N pids:$pids" >> batch2.out
wait $pids
echo "$(date -u +%FT%TZ) batch2 all shards finished" >> batch2.out
