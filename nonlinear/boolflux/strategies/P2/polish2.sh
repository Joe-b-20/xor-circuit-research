#!/bin/bash
# P2 polish job: fdrive under hard caps, then verify + save the best (if it improves on BAR_G at the cap).
#   polish.sh TARGET START CAPA CAPGD MODE SEED SECONDS TAG
set -u
TGT=$1; START=$2; CAPA=$3; CAPGD=$4; MODE=$5; SEED=$6; SECS=$7; TAG=$8
P2=/home/joebachir20/xs-campaigns/2026-11-15-targets/P2
OUT=$P2/runs/$TAG
K=/home/joebachir20/xs-campaigns/2026-11-14-hub/long/bin/bfx-94a75e2c18
cd /home/joebachir20/xcr-boolflux/nonlinear/boolflux
mkdir -p $OUT
CMD="env F_BFX=$K python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P2/fdrive_p2.py --start $START --cap $CAPGD --cap-ad 4 --cap-a $CAPA --mode $MODE --seconds $SECS --seed $SEED --out $OUT"
echo "$CMD" > $OUT/command.txt
T0=$(date +%s)
$CMD > $OUT/fdrive.out 2>&1
T1=$(date +%s)
if [ -f $OUT/best.circ.txt ]; then
  python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P2/save.py $TGT $OUT/best.circ.txt $TAG \
    --start $START --method "strategies/P2/fdrive_p2.py mode $MODE, caps GD$CAPGD AD4 A$CAPA, kernel bfx-94a75e2c18, repair_keep 1" \
    --kernel $K --path-certified true --only-better --command "$CMD" --seed $SEED --elapsed $((T1-T0)) > $OUT/save.txt 2>&1
fi
