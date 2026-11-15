#!/bin/bash
# qsemi.sh CASEFILE NWORKERS WORKER OUTDIR
# CASEFILE lines: "SPEC GAMMA K"  -- semi-member search (all 108,375 X3 tensors) over the stage-1 SPEC:
#  (1) member-seeded gen13 (exhaustive for layers with >= 9 distinct member images),
#  (2) class-seeded gen13c (exhaustive for layers with C(m,2) + sum_c C(s_c,2) >= 32 allowed pairs),
#  fastrank.py rank test; covering sets -> rvd.py (minimise, build, aes_check into found/).
cd ~/xcr-boolflux/nonlinear/boolflux/strategies/H2
CF=$1; NW=$2; WK=$3; OUT=$4; MODE=${5:-ab}   # MODE a = member-seeded only
mkdir -p $OUT/tmp
i=0
while read spec g K; do
  if [ $((i % NW)) -eq $WK ] && [ -n "$spec" ]; then
    P=$OUT/tmp/s$WK
    rm -f $P.img $P.pkl $P.full $P.cls
    python3 rprep.py $spec $g $P semi > $P.prep 2>&1
    if [ ! -f $P.img ]; then echo "$spec gamma=$g K=$K PREP-FAIL $(tail -1 $P.prep)" >> $OUT/s$WK.log
    else
      timeout 3600 ./gen13 $K $(cat $P.n0) < $P.img > $P.a.gsol 2> $P.a.gerr
      ra=$(python3 fastrank.py $P $P.a.gsol)
      [ -s $P.a.gsol.cov ] || : > $P.a.gsol.cov
      rb="skipped"; : > $P.b.gsol; : > $P.b.gsol.cov; echo skipped > $P.b.gerr
      if [ "$MODE" = "ab" ]; then
        timeout 5400 ./gen13c $K 0 $P.cls < $P.img > $P.b.gsol 2> $P.b.gerr
        rb=$(python3 fastrank.py $P $P.b.gsol)
      fi
      v=""
      for x in a b; do
        if [ -s $P.$x.gsol.cov ]; then v="$v $(python3 rvd.py $P $P.$x.gsol.cov 2 2>&1 | tail -3 | tr '\n' ' ')"; cp $P.pkl $OUT/HIT-$i-$x.pkl; cp $P.$x.gsol.cov $OUT/HIT-$i-$x.cov; fi
      done
      echo "$spec gamma=$g K=$K semi: member-seeded [$(tail -1 $P.a.gerr); $ra] class-seeded [$(tail -1 $P.b.gerr); $rb] $v" >> $OUT/s$WK.log
    fi
  fi
  i=$((i + 1))
done < $CF
echo "worker $WK done" >> $OUT/s$WK.log
