#!/bin/bash
# g13case.sh NAME EARLY GAMMAS K GEN [EXTRA...]
#   One exact case with H2's real-model pipeline (read-only use of strategies/H2 code):
#   rprep.py EARLY GAMMAS [EXTRA] -> gen13 K -> fastrank (cover test on full quotient coords)
#   -> rvd_z1.py on covering sets (re-verifies on the 256 inputs, minimises, builds <= 2 into
#   Z1 found/, aes_check).  GEN: g = gen13 all seeds; a = gen13 member-seeded (n0); c = gen13c
#   class-seeded.  One summary line per case in $D/cases.log.
set -u
H2=~/xcr-boolflux/nonlinear/boolflux/strategies/H2
Z1=~/xcr-boolflux/nonlinear/boolflux/strategies/Z1
D=~/xs-campaigns/2026-11-15-targets/Z1/runs/g13
mkdir -p $D ~/xs-campaigns/2026-11-15-targets/Z1/found
NAME=$1; EARLY=$2; GAM=$3; K=$4; GEN=$5; shift 5
P=$D/$NAME
t0=$(date +%s)
cd $H2
if [ ! -f $P.img ]; then
  python3 rprep.py $EARLY $GAM $P "$@" > $P.prep 2>&1
fi
if [ ! -f $P.img ]; then echo "$(date -u +%H:%M:%S) $NAME early=$EARLY gamma=$GAM K=$K PREP-FAIL $(tail -1 $P.prep)" >> $D/cases.log; exit 1; fi
S=$P.K$K.$GEN
case $GEN in
  g) timeout ${G13_TIMEOUT:-3600} ./gen13 $K < $P.img > $S.gsol 2> $S.gerr ;;
  a) timeout ${G13_TIMEOUT:-3600} ./gen13 $K $(cat $P.n0) < $P.img > $S.gsol 2> $S.gerr ;;
  c) timeout ${G13_TIMEOUT:-3600} ./gen13c $K 0 $P.cls < $P.img > $S.gsol 2> $S.gerr ;;
esac
rc=$?
fr=$(python3 fastrank.py $P $S.gsol)
v=""
if [ -s $S.gsol.cov ]; then v=$(python3 $Z1/rvd_z1.py $P $S.gsol.cov 2 2>&1 | tee $S.rvd | grep -E "total ANDs 2[0-7]$|OK|FAIL|distinct" | tr '\n' ' '); fi
t1=$(date +%s)
echo "$(date -u +%H:%M:%S) $NAME early=$EARLY gamma=$GAM K=$K gen=$GEN extra=$* rc=$rc | $(tail -1 $P.prep) | $(tail -1 $S.gerr) | $fr | $v | $((t1-t0))s" >> $D/cases.log
ls ~/xs-campaigns/2026-11-15-targets/Z1/found/z1g13-$NAME-[0-9a-f]*-s*.circ.txt 2>/dev/null | xargs -r python3 $Z1/sidecar.py >> $D/sidecar.log 2>&1
