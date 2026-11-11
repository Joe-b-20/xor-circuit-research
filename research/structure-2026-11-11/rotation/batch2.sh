#!/bin/bash
# Parallel SAT jobs (one core each), all with hard time limits.
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
ulimit -v 8000000
mkdir -p logs circuits
(timeout 900 python3 run_sat.py 2 13 18 --out circuits/f2_opt.txt > logs/f2_sat.log 2>&1; echo "exit $?" >> logs/f2_sat.log) &
(timeout 150 python3 periodic_sat.py 4 0 12 --verify 4,5,6,7,8 > logs/per_shift4_k12.log 2>&1; echo "exit $?" >> logs/per_shift4_k12.log) &
(timeout 400 python3 periodic_sat.py 4 1 10 --verify 4,8,12 --out circuits/screw4_k10.txt > logs/per_screw4_k10.log 2>&1; echo "exit $?" >> logs/per_screw4_k10.log) &
(timeout 400 python3 periodic_sat.py 4 0 10 --verify 4,5,6,7,8 --out circuits/shift4_k10.txt > logs/per_shift4_k10.log 2>&1; echo "exit $?" >> logs/per_shift4_k10.log) &
wait
tail -n 30 logs/f2_sat.log logs/per_shift4_k12.log logs/per_screw4_k10.log logs/per_shift4_k10.log
