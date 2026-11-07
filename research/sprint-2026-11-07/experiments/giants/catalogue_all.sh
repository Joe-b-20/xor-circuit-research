#!/bin/bash
# Parallel exact 88-plateau catalogue of every sampled 88 state (hunt samples A/B, C, D) plus the
# 8 unresolved giant seeds.  PREPARED, NOT LAUNCHED.  Usage: catalogue_all.sh [N=16]
#   1. cat_prep.py   queue (giants first, time_limit 1800; then samples interleaved across chains,
#                    time_limit 900) + products.json; clears stale claims -> resumable
#   2. N x cat_worker.py k   (nice -n 5), disjoint seeds by exclusive claim files, one
#                    catalogue/shard_k.jsonl each; lookup first (4 rotations, all known plateaus,
#                    refreshed from other shards' pl files), compress only non-members
#   3. cat_merge.py  plateaus_all.json, landings_all.json, landing_table_all.txt,
#                    reestimate_all.out (Chao2, D2, chain-pair N_eff, alpha, HT)
# Stop cleanly: touch giants/STOP (each worker finishes its current item, then exits; the merge
# still runs on what is done).  Re-run the script to resume (rm STOP first).
set -u
N=${1:-16}
G=/home/joebachir20/xs-campaigns/2026-11-07-sprint/giants
CAT=$G/catalogue
mkdir -p "$CAT/logs"
cd "$G" || exit 1
if [ -e "$G/STOP" ]; then echo "giants/STOP exists: remove it to run"; exit 1; fi
echo "$(date -u +%FT%TZ) prep" | tee -a "$CAT/logs/run.log"
nice -n 5 python3 cat_prep.py 2>&1 | tee -a "$CAT/logs/run.log" || exit 1
pids=()
for k in $(seq 0 $((N - 1))); do
  nice -n 5 python3 cat_worker.py "$k" > "$CAT/logs/shard_$k.log" 2>&1 &
  pids+=($!)
done
echo "$(date -u +%FT%TZ) started $N workers: ${pids[*]}" | tee -a "$CAT/logs/run.log"
fail=0
for p in "${pids[@]}"; do wait "$p" || fail=$((fail + 1)); done
echo "$(date -u +%FT%TZ) workers done (nonzero exits: $fail)" | tee -a "$CAT/logs/run.log"
nice -n 5 python3 cat_merge.py 2>&1 | tee -a "$CAT/logs/run.log"
echo "$(date -u +%FT%TZ) merge done" | tee -a "$CAT/logs/run.log"
