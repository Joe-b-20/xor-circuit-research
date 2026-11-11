#!/bin/bash
cd ~/xor-circuit-research/research/structure-2026-11-11/review-charges
for i in $(seq 1 330); do
  n=$(pgrep -fc 'lemma_sat.py|q4_sym.py')
  if [ "$n" = 0 ]; then
    echo ALLDONE
    cat sat9_nosym.log q4sym_step1.log q4sym_step2.log
    exit 0
  fi
  sleep 5
done
echo STILL-RUNNING
