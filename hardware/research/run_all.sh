#!/usr/bin/env bash
# The whole study, in order: about 5 hours on 19 cores, most of it the larger circuits.
# Steps 1-2 need the local campaign archives (~/xs-campaigns, ~/xcr-*) and were run once; their
# outputs (candidates/, sample.json, screen.json, lists/, inventory/summary*.json) are committed,
# so a fresh checkout starts at step 3.
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

# 3. base run: both libraries, all three flows; the 41 circuits with G >= 400 (mostly
#    machine-synthesised S-boxes) on Nangate45 and SKY130 preserve only (their SKY130 free-flow
#    routing takes 30-60 min per job)
python3 run.py --list lists/candidates-small.txt --variant base -j "$J"
python3 run.py --list lists/candidates-large.txt --variant base -p nangate45 -j "$J"
python3 run.py --list lists/candidates-large.txt --variant base -p sky130hd -f preserve -j "$J"
python3 run.py --list lists/screen.txt --variant base -j "$J"

# 4. collect and analyse the base run; select_seeds.py chose lists/seeds*.txt (run once, see there)
python3 collect.py
python3 analyze.py
# python3 select_seeds.py

# 5. seeded repeats: placement seeds on every flow, synthesis-order seeds on the free flows
for s in 1 2 3; do
  python3 run.py --list lists/seeds-small.txt --variant pnr$s -j "$J"
  python3 run.py --list lists/seeds-large.txt --variant pnr$s -p nangate45 -j "$J"
  python3 run.py --list lists/seeds-large.txt --variant pnr$s -p sky130hd -f preserve -j "$J"
done
for s in 1 2; do
  python3 run.py --list lists/seeds-small.txt --variant synth$s -f free,free-area -j "$J"
  python3 run.py --list lists/seeds-large.txt --variant synth$s -p nangate45 -f free,free-area -j "$J"
done

# 6. data, analyses, tables
python3 collect.py
python3 analyze.py
python3 seeded.py
python3 tables.py
python3 timing.py
