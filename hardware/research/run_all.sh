#!/usr/bin/env bash
# The whole study, in order: about 6 hours on 19 cores if nothing is cached, most of it the
# larger circuits.  Every step stops the script on a failure (set -e; run.py, bench.py,
# manifest.py, collect.py and electrical.py exit with status 1 on a failed, missing or stale job).
# Needs: hardware/tools/install.sh (Yosys, ABC, OpenROAD, the two libraries) and Python 3.10+
# with numpy and scipy (analyze.py, seeded.py, electrical.py).
# Steps 1-2 need the local campaign archives (~/xs-campaigns, ~/xcr-*) and were run once; their
# outputs (candidates/, sample.json, screen.json, lists/, inventory/summary*.json) are committed,
# so a fresh checkout starts at step 3.  Jobs whose results exist with a matching fingerprint are
# not rerun (manifest.py says which jobs the results must contain).
set -euo pipefail
cd "$(dirname "$0")"
J=${J:-19}

# 1. inventory of every circuit on this machine (inventory/pool.jsonl.gz, summary.json).  The
#    sample was drawn from the version-1 pool (pool-v1.jsonl.gz, summary-v1.json), before the
#    structure hash folded constant operands; collect.py marks the 4 candidates that are
#    duplicates under the folded hash and every analysis leaves them out.
# python3 inventory.py -j "$J"
# 2. the sample and the prospective screen
# python3 sample.py
# python3 screen.py

# 3. the benchmark's own 340 circuits (stage baseline: 2,040 jobs in hardware/build/)
python3 ../bench.py run --suite all -j "$J"

# 4. base run (stage base): the candidates and the screen on both libraries and all three flows;
#    the 41 circuits with G >= 400 on Nangate45 and SKY130 preserve only (their SKY130 free-flow
#    routing takes 30-60 min per job), plus the jobs of lists/extra.txt
python3 run.py --stage base -j "$J"
python3 manifest.py --stage baseline,base          # every base result present and current
# select_seeds.py chose lists/seeds*.txt from the base run once (README, Reproducibility; its
# inputs then were an earlier state of the base run).  To apply its rule to the complete base run:
# python3 collect.py --stage baseline,base --out build/base-results
# python3 analyze.py --res build/base-results
# python3 select_seeds.py --res build/base-results --out build/base-results/lists

# 5. repeats (stage repeats: placement seeds pnr1-3 on every flow, statement-order seeds
#    synth1-2 on the free flows, and the seed-test jobs of lists/extra.txt) and the balanced
#    orders x placements design (stage balanced: lists/balanced.txt)
python3 run.py --stage repeats -j "$J"
python3 run.py --stage balanced -j "$J"

# 6. data (collect.py checks the whole manifest first and writes nothing if a job is missing
#    or stale), analyses, tables.  Everything is written to a staging folder first and copied
#    into results/ only when every step has succeeded, so results/ is never a mixed set.
#    (timing.py reads the committed results/screen_cost.json; timing.py --measure-screen 60
#    remeasures it, about 12 minutes on 4 otherwise idle cores.)
S=build/results-staging
rm -rf "$S"
mkdir -p "$S"
cp results/screen_cost.json results/revalidation.json "$S"/
export HWRESEARCH_RESULTS="$PWD/$S"
python3 collect.py
python3 analyze.py
python3 seeded.py
python3 tables.py
python3 electrical.py
python3 timing.py
unset HWRESEARCH_RESULTS
cp "$S"/* results/
echo "results/ updated from $S"
