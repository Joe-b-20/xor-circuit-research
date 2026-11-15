#!/bin/bash
# usage: jsweep.sh EARLY LATE "EK pairs" TIMEOUT
cd ~/xcr-boolflux/nonlinear/boolflux/strategies/H2
D=~/xs-campaigns/2026-11-15-study/H2/jsat
mkdir -p $D
for g in 0 1 4 5 6 7 2 3 8 9 10 11 12 13 14 15; do
  for ek in $3; do
    E=${ek%,*}; K=${ek#*,}
    out=$D/$1-$2-g$g-E$E-K$K.json
    r=$(timeout $4 python3 -u jsat.py --gamma $g --early $1 --late $2 --E $E --K $K --out $out 2>&1 | grep -E "RESULT|Error|Trace" | tr '\n' ' ')
    echo "$1 $2 gamma=$g E=$E K=$K : ${r:-TIMEOUT}"
  done
done
