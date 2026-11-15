#!/bin/bash
# genbatch.sh EARLYSPEC TAG K gamma...   (prep + gen13 + vd13 verification/build of up to 2 circuits)
cd ~/xcr-boolflux/nonlinear/boolflux/strategies/H2
D=~/xs-campaigns/2026-11-15-study/H2/d13
E=$1; TAG=$2; K=$3; shift 3
for g in "$@"; do
  P=$D/$TAG-g$g
  [ -f $P.txt.img ] || python3 d13prep.py $E $g $P.txt > $P.prep 2>&1
  timeout 1800 ./gen13 $K < $P.txt.img > $P.K$K.gsol 2> $P.K$K.gerr
  ns=$(grep -c SOL $P.K$K.gsol)
  v=""
  if [ "$ns" -gt 0 ]; then v=$(python3 vd13.py $P 2 $P.K$K.gsol 2>&1 | tail -1); fi
  echo "$TAG gamma=$g K=$K: $(tail -1 $P.K$K.gerr) | cand $ns | $v"
done
