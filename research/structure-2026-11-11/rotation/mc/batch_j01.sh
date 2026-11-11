#!/bin/bash
# Joint sheets 0/1 SAT, cases b and c1 (25 CPU-minutes each at most), two cores.
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
ulimit -v 8000000
(timeout 1500 python3 j01_sat.py b > logs/j01_b.log 2>&1; echo "exit_$?" >> logs/j01_b.log) &
(timeout 1500 python3 j01_sat.py c1 > logs/j01_c1.log 2>&1; echo "exit_$?" >> logs/j01_c1.log) &
wait
head -n 3 logs/j01_b.log logs/j01_c1.log
