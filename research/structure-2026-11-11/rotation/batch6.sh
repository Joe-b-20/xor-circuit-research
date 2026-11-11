#!/bin/bash
# Batch 6: Q_8 plus one / two of the MixColumns extra terms (heuristic), and the three period-1 instances
# that timed out at 25 s.
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
ulimit -v 8000000
(bash run_quick.sh 8 420 x17 0 1:7 > logs/quick_q8_x17.log 2>&1) &
(bash run_quick.sh 8 420 x17x37 0 1:7,3:7 > logs/quick_q8_x17x37.log 2>&1) &
(for O in s0,s1,s3 s1,s3,s2 s0,s3,s2; do echo "P = s0,s1,s3 -> O = $O"; timeout 150 python3 scheme_sat.py s0,s1,s3 $O | head -n 1; echo "exit $?"; done > logs/scheme_period1_rest.log 2>&1) &
wait
head -n 2 logs/quick_q8_x17.log logs/quick_q8_x17x37.log
cat logs/scheme_period1_rest.log
