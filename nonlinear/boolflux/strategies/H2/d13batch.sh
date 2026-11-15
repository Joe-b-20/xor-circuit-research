#!/bin/bash
# d13batch.sh EARLYSPEC TAG NEED gamma...
cd ~/xcr-boolflux/nonlinear/boolflux/strategies/H2
D=~/xs-campaigns/2026-11-15-study/H2/d13
E=$1; TAG=$2; NEED=$3; shift 3
for g in "$@"; do
  python3 d13prep.py $E $g $D/$TAG-g$g.txt > $D/$TAG-g$g.prep 2>&1
  ./d13 $NEED < $D/$TAG-g$g.txt > $D/$TAG-g$g.sol 2> $D/$TAG-g$g.err
  echo "$TAG gamma=$g prep: $(cat $D/$TAG-g$g.prep | tail -1) | $(tail -1 $D/$TAG-g$g.err) | SOL lines $(grep -c SOL $D/$TAG-g$g.sol)"
done
