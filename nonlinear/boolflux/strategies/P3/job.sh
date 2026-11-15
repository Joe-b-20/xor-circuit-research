#!/bin/bash
# P3 job: pdrive.py (fdrive + hard A/AD guard) under caps A<=32, AD<=4, GD<=CAPGD, then record.py of the best.
#   job.sh START MODE CAPGD SEED SECS TAG [extra pdrive args...]
set -u
START=$1; MODE=$2; CAPGD=$3; SEED=$4; SECS=$5; TAG=$6; shift 6
P3=/home/joebachir20/xs-campaigns/2026-11-15-targets/P3
OUT=$P3/runs/$TAG
K=/home/joebachir20/xs-campaigns/2026-11-15-targets/P3/bin/bfx-4dc199db   # repo kernel/bfx (bfx.c sha256 c8d293b6, has repair_keep); from 18:25 UTC
S=/home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P3
mkdir -p $OUT
cd /home/joebachir20/xcr-boolflux/nonlinear/boolflux
CMD="env F_BFX=$K python3 $S/pdrive.py --start $START --cap $CAPGD --cap-ad 4 --cap-a 32 --mode $MODE --seconds $SECS --seed $SEED --out $OUT $*"
echo "$CMD" > $OUT/command.txt
T0=$(date +%s)
$CMD > $OUT/pdrive.out 2>&1
T1=$(date +%s)
if [ -f $OUT/best.circ.txt ]; then
  python3 $S/record.py --circ $OUT/best.circ.txt --start $START --tag $TAG \
    --method "pdrive (strategies/F/fdrive.py + hard A/AD guard) mode $MODE, caps A32 AD4 GD$CAPGD, kernel bfx-4dc199db, repair_keep 1" \
    --command "$CMD" --seed $SEED --elapsed $((T1-T0)) --kernel $K --path-certified true ${REPRO:+--reproduces $REPRO} > $OUT/record.txt 2>&1
fi
for P in $OUT/pareto/*.circ.txt; do
  [ -f "$P" ] || continue
  python3 $S/record.py --circ $P --start $START --tag $TAG \
    --method "pdrive (strategies/F/fdrive.py + hard A/AD guard) mode $MODE, caps A32 AD4 GD$CAPGD, kernel bfx-4dc199db, repair_keep 1 (run Pareto set)" \
    --command "$CMD" --seed $SEED --elapsed $((T1-T0)) --kernel $K --path-certified true ${REPRO:+--reproduces $REPRO} >> $OUT/record-pareto.txt 2>&1
done
echo done > $OUT/DONE
