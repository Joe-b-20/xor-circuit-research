#!/bin/bash
# Batch 3 (at most 4 cores): period-1 sheet schemes; heuristic runs for Q_5, Q_7 and for extra terms.
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
ulimit -v 8000000
mkdir -p logs
(python3 scheme_sat.py --period1 25 > logs/scheme_period1.log 2>&1) &
(bash run_quick.sh 5 240 a 0 > logs/quick_q5_a.log 2>&1; bash run_quick.sh 4 150 x11 0 1:1 > logs/quick_q4_x11.log 2>&1) &
(bash run_quick.sh 7 360 a 0 > logs/quick_q7_a.log 2>&1) &
(bash run_quick.sh 4 150 x13 0 1:3 > logs/quick_q4_x13.log 2>&1; bash run_quick.sh 4 150 x12 0 1:2 > logs/quick_q4_x12.log 2>&1; bash run_quick.sh 6 240 x20 0 2:0 > logs/quick_q6_x20.log 2>&1) &
wait
head -n 2 logs/quick_q5_a.log logs/quick_q7_a.log logs/quick_q4_x11.log logs/quick_q4_x13.log logs/quick_q4_x12.log logs/quick_q6_x20.log
cat logs/scheme_period1.log
