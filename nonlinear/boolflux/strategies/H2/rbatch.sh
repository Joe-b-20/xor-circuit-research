#!/bin/bash
# rbatch.sh LISTFILE GAMMASETS : each list line "SPEC TAG K"; GAMMASETS e.g. "0 1 2 ... 15" (each item may be a comma list)
cd ~/xcr-boolflux/nonlinear/boolflux/strategies/H2
D=~/xs-campaigns/2026-11-15-study/H2/real
LIST=$1; shift
while read spec tag K ex; do
  [ -z "$spec" ] && continue
  for g in "$@"; do
    P=$D/$tag-g${g//,/_}
    [ -f $P.img ] || python3 rprep.py $spec $g $P $ex > $P.prep 2>&1
    if [ ! -f $P.img ]; then echo "$tag gamma=$g PREP FAILED: $(tail -1 $P.prep)"; continue; fi
    timeout 1800 ./gen13 $K < $P.img > $P.K$K.gsol 2> $P.K$K.gerr
    ns=$(grep -c SOL $P.K$K.gsol); v=""
    if [ "$ns" -gt 0 ]; then v=$(python3 rvd.py $P $P.K$K.gsol 2 2>&1 | tail -1); fi
    echo "$tag gamma=$g K=$K: $(head -1 $P.prep | cut -c1-60) | $(tail -1 $P.K$K.gerr) | cand $ns | $v"
  done
done < $LIST
