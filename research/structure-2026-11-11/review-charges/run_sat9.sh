#!/bin/bash
cd ~/xor-circuit-research/research/structure-2026-11-11/review-charges
ulimit -v 8000000
mode=$1
if [ "$mode" = "sym" ]; then
  timeout 1200 python3 lemma_sat.py 9 --sym > sat9_sym.log 2>&1
elif [ "$mode" = "symg" ]; then
  timeout 1200 python3 lemma_sat.py 9 --sym --solver glucose4 > sat9_sym_glucose.log 2>&1
else
  timeout 1150 python3 lemma_sat.py 9 > sat9_nosym.log 2>&1
fi
echo "exit $?" >> sat9_$mode.done
