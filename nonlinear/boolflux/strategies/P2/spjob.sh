#!/bin/bash
# P2 skeleton-pull job: sp.py then verify + save if better than the start.
#   spjob.sh TARGET START CAPA CAPGD SEED SECONDS TAG [RELAX]
set -u
TGT=$1; START=$2; CAPA=$3; CAPGD=$4; SEED=$5; SECS=$6; TAG=$7; RELAX=${8:-1}
P2=/home/joebachir20/xs-campaigns/2026-11-15-targets/P2
OUT=$P2/runs/$TAG
K=/home/joebachir20/xs-campaigns/2026-11-14-hub/long/bin/bfx-593fa798f5
cd /home/joebachir20/xcr-boolflux/nonlinear/boolflux
mkdir -p $OUT
CMD="env F_BFX=$K python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P2/sp.py --start $START --cap $CAPGD --cap-a $CAPA --cap-ad 4 --seconds $SECS --seed $SEED --relax $RELAX --out $OUT"
echo "$CMD" > $OUT/command.txt
T0=$(date +%s); $CMD > $OUT/sp.out 2>&1; T1=$(date +%s)
if [ -f $OUT/best.circ.txt ]; then
  python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P2/save.py $TGT $OUT/best.circ.txt $TAG     --start $START --method "strategies/P2/sp.py skeleton pull (kernel at cap+$RELAX, skeleton bound check, P2 dsynth rebuild with parent reuse, kernel at cap), caps GD$CAPGD AD4 A$CAPA, kernel bfx-593fa798f5"     --only-better --command "$CMD" --seed $SEED --elapsed $((T1-T0)) > $OUT/save.txt 2>&1
fi
