#!/bin/bash
# Gadget SAT sweep: gsweep.sh OUTDIR CIRC "k:budget k:budget ..." [TIMEOUT]
OUT=$1; C=$2; LIST="4:20 5:8"; TO=600  # 16:47: 5:10 SAT (builds 126-127), 5:9 skipped
R=/home/joebachir20/xs-campaigns/2026-11-15-targets/P3/starts/a32-ad4-g117-gd19-79bccd2434fd.circ.txt
mkdir -p $OUT; cd $OUT
for kb in $LIST; do
  k=${kb%%:*}; b=${kb##*:}
  echo "$(date -u +%T) k $k budget $b"
  rm -f gadget-sols.json
  timeout $TO python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P3/gadget.py $R $C --k $k --budget $b --nsol 3 2>&1 | cut -c1-800
  echo "$(date -u +%T) exit $?"
  [ -f gadget-sols.json ] && cp gadget-sols.json sols-k$k-b$b.json
done
