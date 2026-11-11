#!/bin/bash
cd ~/xor-circuit-research/research/structure-2026-11-11/review-charges
ulimit -v 8000000
for s in 11 12 13; do timeout 1100 python3 perturb.py $s 1500 > perturb_$s.log 2>&1 & done
wait
cat perturb_1*.log
