#!/bin/bash
# X3b: 11 + 2 / 10 + 3 style windows of H2's s59 14-layer: fixed prefix (fixk) and stage 1 free (fixkq), O2.
D=~/xcr-boolflux/nonlinear/boolflux/strategies/X3
F=h2-ad4a-g1-c8c7227f-s59-a28.circ.txt
for w in "$@"; do
  echo -n "fixed  $w: "; bash $D/x3b_fixk.sh $F $w O2 0:262144 | grep -o '"d": [0-9]*\|"reached": [0-9]*\|"complete": [a-z]*\|"reach_idx": [^]]*\]' | tr '\n' ' '; echo
  echo -n "free   $w: "; bash $D/x3b_fixkq.sh $F $w O2 0 18
done
