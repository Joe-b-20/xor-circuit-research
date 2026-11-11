#!/bin/bash
# Batch 5: chained schemes for all m; sheet cost with every vector of the previous block free; last block.
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
ulimit -v 8000000
(timeout 600 python3 walks.py 40 > logs/walks.log 2>&1; echo "exit $?" >> logs/walks.log) &
(timeout 600 python3 free_prev.py --odd outputs 9 10 > logs/free_outputs_odd.log 2>&1; echo "exit $?" >> logs/free_outputs_odd.log) &
(for K in 11 12; do echo "last block, K = $K"; timeout 400 python3 free_prev.py one s0,s1,s2,s3 $K; echo "exit $?"; done > logs/free_last2.log 2>&1) &
wait
cat logs/walks.log logs/free_outputs_odd.log logs/free_last2.log
