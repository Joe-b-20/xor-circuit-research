#!/bin/bash
# qworker2.sh CASEFILE NWORKERS WORKER OUTDIR
# CASEFILE lines: "SPEC GAMMAS K [EXTRA...]"  (GAMMAS = comma list mixed in one layer; EXTRA passed to rprep.py,
# e.g. bil or midfile:PATH).  Lines i with i % NWORKERS == WORKER.  One summary line per case in OUTDIR/w$WORKER.log;
# verified circuits (if any) -> strategies/H2/found/ (aes_check run by rvd.py).
cd ~/xcr-boolflux/nonlinear/boolflux/strategies/H2
CF=$1; NW=$2; WK=$3; OUT=$4
mkdir -p $OUT/tmp
i=0
while read spec g K ex; do
  if [ $((i % NW)) -eq $WK ] && [ -n "$spec" ]; then
    P=$OUT/tmp/w$WK
    rm -f $P.img $P.pkl
    python3 rprep.py $spec $g $P $ex > $P.prep 2>&1
    if [ ! -f $P.img ]; then echo "$spec gamma=$g K=$K $ex PREP-FAIL $(tail -1 $P.prep)" >> $OUT/w$WK.log
    else
      timeout 3600 ./gen13 $K < $P.img > $P.gsol 2> $P.gerr
      ns=$(grep -c SOL $P.gsol); v=""
      if [ "$ns" -gt 0 ]; then v=$(python3 rvd.py $P $P.gsol 2 2>&1 | tail -3 | tr '\n' ' '); fi
      echo "$spec gamma=$g K=$K $ex: $(head -1 $P.prep | cut -c1-40) | $(tail -1 $P.gerr) | cand $ns | $v" >> $OUT/w$WK.log
      if echo "$v" | grep -q "distinct covering minimal [1-9]"; then cp $P.pkl $OUT/HIT-$i.pkl; cp $P.gsol $OUT/HIT-$i.gsol; fi
    fi
  fi
  i=$((i + 1))
done < $CF
echo "worker $WK done" >> $OUT/w$WK.log
