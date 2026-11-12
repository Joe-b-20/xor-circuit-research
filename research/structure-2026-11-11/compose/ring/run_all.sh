#!/bin/bash
# CHECK driver: exit summary for recorded rotation circuits (both summation orders).
cd ~/xor-circuit-research/research/structure-2026-11-11
ulimit -v 8000000
for c in q5_50:5 walk_q5_50:5 q6_60:6 q8_80:8; do
  for o in fwd rev; do
    out=$(python3 compose/ring/ring_cuts.py rotation/circuits/${c%%:*}.txt ${c##*:} $o)
    echo "$out" | head -3
    echo "  arc cuts with exits: $(echo "$out" | grep -c 'exits [1-9]')"
    echo "$out" | grep '^arc \[[0-9]\]:' | cut -c1-90
  done
done
