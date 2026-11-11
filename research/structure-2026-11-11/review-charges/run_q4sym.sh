#!/bin/bash
cd ~/xor-circuit-research/research/structure-2026-11-11/review-charges
ulimit -v 8000000
(timeout 600 python3 q4_sym.py 1 10; timeout 600 python3 q4_sym.py 1 9) > q4sym_step1.log 2>&1 &
(timeout 900 python3 q4_sym.py 2 19) > q4sym_step2.log 2>&1 &
wait
cat q4sym_step1.log q4sym_step2.log
