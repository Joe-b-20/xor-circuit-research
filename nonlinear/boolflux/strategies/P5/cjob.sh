#!/bin/bash
# P5 job: p3_pdrive.py (copy of P3's fdrive + hard A/AD guard) under caps A<=32, AD<=CAPAD,
# GD<=CAPGD; then rec.py on the best and on every file of the run's (G, GD) Pareto set.
#   cjob.sh START CAPAD CAPGD MODE SEED SECS TAG
set -u
START=$1; CAPAD=$2; CAPGD=$3; MODE=$4; SEED=$5; SECS=$6; TAG=$7
P5=/home/joebachir20/xs-campaigns/2026-11-15-targets/P5
S=/home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P5
OUT=$P5/runs/$TAG
K=/home/joebachir20/xs-campaigns/2026-11-14-hub/long/bin/bfx-94a75e2c18
mkdir -p $OUT
cd /home/joebachir20/xcr-boolflux/nonlinear/boolflux
CMD="env F_BFX=$K python3 $S/p3_pdrive.py --start $START --cap $CAPGD --cap-ad $CAPAD --cap-a 32 --mode $MODE --seconds $SECS --seed $SEED --out $OUT"
echo "$CMD" > $OUT/command.txt
T0=$(date +%s)
$CMD > $OUT/pdrive.out 2>&1
EL=$(( $(date +%s) - T0 ))
METH="p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode $MODE, caps A<=32 AD<=$CAPAD GD<=$CAPGD, kernel bfx-94a75e2c18 repair_keep 1"
for C in $OUT/best.circ.txt $OUT/pareto/*.circ.txt; do
  [ -f "$C" ] || continue
  python3 $S/rec.py --circ $C --start $START --tag $TAG --capad $CAPAD --method "$METH" \
     --command "$CMD" --seed $SEED --elapsed $EL --kernel $K >> $OUT/record.txt 2>&1
done
echo done > $OUT/DONE
