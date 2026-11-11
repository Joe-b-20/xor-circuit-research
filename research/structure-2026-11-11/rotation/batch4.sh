#!/bin/bash
# Batch 4: sheet cost with the whole even space of the previous block free (three cores).
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
ulimit -v 8000000
(timeout 500 python3 free_prev.py outputs 5 10 > logs/free_outputs.log 2>&1; echo "exit $?" >> logs/free_outputs.log) &
(for K in 8 9 10; do echo "last block, K = $K"; timeout 240 python3 free_prev.py one s0,s1,s2,s3 $K; echo "exit $?"; done > logs/free_last.log 2>&1) &
(timeout 600 python3 free_prev.py basis 9 70 > logs/free_basis9.log 2>&1; echo "exit $?" >> logs/free_basis9.log) &
wait
cat logs/free_outputs.log logs/free_last.log logs/free_basis9.log
