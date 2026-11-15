#!/bin/bash
# qworker.sh SPECFILE NWORKERS WORKER K OUTDIR GAMMAS...
# Processes lines i of SPECFILE with i % NWORKERS == WORKER (each line: an early spec, e.g. kara:...),
# for each gamma: rprep (real model) -> gen13 K -> rvd (verify, minimise, build <= 2 circuits into found/,
# aes_check).  Appends one summary line per (spec, gamma) to OUTDIR/w$WORKER.log.
cd ~/xcr-boolflux/nonlinear/boolflux/strategies/H2
SPECS=$1; NW=$2; WK=$3; K=$4; OUT=$5; shift 5
mkdir -p $OUT/tmp
i=0
while read spec; do
  if [ $((i % NW)) -eq $WK ] && [ -n "$spec" ]; then
    for g in "$@"; do
      P=$OUT/tmp/w$WK
      rm -f $P.img $P.pkl
      python3 rprep.py $spec $g $P > $P.prep 2>&1
      if [ ! -f $P.img ]; then echo "$spec gamma=$g PREP-FAIL $(tail -1 $P.prep)" >> $OUT/w$WK.log; continue; fi
      timeout 1800 ./gen13 $K < $P.img > $P.gsol 2> $P.gerr
      ns=$(grep -c SOL $P.gsol); v=""
      if [ "$ns" -gt 0 ]; then v=$(python3 rvd.py $P $P.gsol 2 2>&1 | tail -3 | tr '\n' ' '); fi
      echo "$spec gamma=$g K=$K: $(tail -1 $P.gerr) | cand $ns | $v" >> $OUT/w$WK.log
      if echo "$v" | grep -q "distinct covering minimal [1-9]"; then cp $P.pkl $OUT/HIT-$(echo $spec | tr ':,/' '___')-g$g.pkl; cp $P.gsol $OUT/HIT-$(echo $spec | tr ':,/' '___')-g$g.gsol; fi
    done
  fi
  i=$((i + 1))
done < $SPECS
echo "worker $WK done" >> $OUT/w$WK.log
