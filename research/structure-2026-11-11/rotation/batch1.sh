#!/bin/bash
# Three heuristic runs in parallel (one core each): Q_4 seed 1 (300 s), Q_6 (300 s), Q_8 (400 s).
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
mkdir -p logs
bash run_quick.sh 4 300 b 1 > logs/quick_q4_b.log 2>&1 &
bash run_quick.sh 6 300 a 0 > logs/quick_q6_a.log 2>&1 &
bash run_quick.sh 8 400 a 0 > logs/quick_q8_a.log 2>&1 &
wait
head -n 3 logs/quick_q4_b.log logs/quick_q6_a.log logs/quick_q8_a.log
