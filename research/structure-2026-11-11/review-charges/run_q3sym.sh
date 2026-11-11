#!/bin/bash
cd ~/xor-circuit-research/research/structure-2026-11-11/review-charges
ulimit -v 8000000
timeout 400 python3 q4_sym.py 1 10 3 q3_sym30.txt
if [ -f q3_sym30.txt ]; then python3 q3_check.py q3_sym30.txt 3 | head -3; fi
python3 q3_check.py ../rotation/circuits/q8_80.txt 8 | head -3
