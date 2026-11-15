#!/bin/bash
# qall2.sh CASEFILE NWORKERS WORKER OUTDIR
# CASEFILE lines: "SPEC GAMMA K". Candidates = members + X3's semi-members + X3b's 2.16M singleton-coset tensors
# (rprep options semi all2); class-seeded gen13c (seed pairs: member pairs + pairs of non-members in one class
# mod M8) -- exhaustive for layers with C(m,2) + sum_c C(s_c,2) >= 32; fastrank; covering -> rvd (build + aes_check).
cd ~/xcr-boolflux/nonlinear/boolflux/strategies/H2
CF=$1; NW=$2; WK=$3; OUT=$4
mkdir -p $OUT/tmp
i=0
while read spec g K; do
  if [ $((i % NW)) -eq $WK ] && [ -n "$spec" ]; then
    P=$OUT/tmp/a$WK
    rm -f $P.img $P.pkl $P.full $P.cls
    python3 rprep.py $spec $g $P semi all2 > $P.prep 2>&1
    if [ ! -f $P.img ]; then echo "$spec gamma=$g K=$K PREP-FAIL $(tail -1 $P.prep)" >> $OUT/a$WK.log
    else
      timeout 10800 ./gen13c $K 0 $P.cls < $P.img > $P.b.gsol 2> $P.b.gerr
      rb=$(python3 fastrank.py $P $P.b.gsol); v=""
      if [ -s $P.b.gsol.cov ]; then v=$(python3 rvd.py $P $P.b.gsol.cov 2 2>&1 | tail -3 | tr '\n' ' '); cp $P.pkl $OUT/HIT-$i.pkl; cp $P.b.gsol.cov $OUT/HIT-$i.cov; fi
      echo "$spec gamma=$g K=$K semi+singletons class-seeded: [$(tail -1 $P.b.gerr); $rb] $v" >> $OUT/a$WK.log
    fi
  fi
  i=$((i + 1))
done < $CF
echo "worker $WK done" >> $OUT/a$WK.log
