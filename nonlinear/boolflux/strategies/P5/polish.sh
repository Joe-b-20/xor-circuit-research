#!/bin/bash
# P5 polish job: fdrive.py under hard caps A<=32, AD<=CAP_AD, GD<=CAP_GD; then aes_check of the best
# and, when it verifies, a copy into found/ with the full sidecar (BRIEF "What to save").
#   polish.sh START CAP_AD CAP_GD MODE SEED SECONDS TAG
set -u
START=$1; CAPAD=$2; CAPGD=$3; MODE=$4; SEED=$5; SECS=$6; TAG=$7
P5=/home/joebachir20/xs-campaigns/2026-11-15-targets/P5
OUT=$P5/runs/pol-$TAG
K=/home/joebachir20/xs-campaigns/2026-11-14-hub/long/bin/bfx-593fa798f5
BF=/home/joebachir20/xcr-boolflux/nonlinear/boolflux
cd $BF
mkdir -p $OUT
T0=$(date +%s)
CMD="env F_BFX=$K python3 $BF/strategies/F/fdrive.py --start $START --cap $CAPGD --cap-ad $CAPAD --cap-a 32 --mode $MODE --seconds $SECS --seed $SEED --out $OUT"
echo "$CMD" > $OUT/command.txt
$CMD > $OUT/fdrive.out 2>&1
EL=$(( $(date +%s) - T0 ))
if [ -f $OUT/best.circ.txt ]; then
  python3 campaigns/aes_check.py $OUT/best.circ.txt > $OUT/aes_check.txt 2>&1
  if head -1 $OUT/aes_check.txt | grep -q '^OK'; then
    read A AD G GD <<< "$(head -1 $OUT/aes_check.txt | sed 's/.*= //' | awk '{print $1, $2, $3, $4}')"
    if [ "$A" -le 32 ] && [ "$AD" -le "$CAPAD" ]; then
      NAME=p5-$TAG-a$A-ad$AD-g$G-gd$GD
      cp $OUT/best.circ.txt $P5/found/$NAME.circ.txt
      SHA=$(sha256sum $START | cut -d" " -f1)
      CODE=$(git -C /home/joebachir20/xcr-boolflux rev-parse --short HEAD)
      KSHA=$(sha256sum $K | cut -d" " -f1)
      OKL=$(head -1 $OUT/aes_check.txt | tr -d '"' | tr -s ' ')
      cat > $P5/found/$NAME.json <<JSON
{"target": "T05", "A": $A, "AD": $AD, "G": $G, "GD": $GD,
 "start": {"path": "$START", "sha256": "$SHA"},
 "method": "strategies/F/fdrive.py mode $MODE, hard caps A<=32 AD<=$CAPAD GD<=$CAPGD, kernel bfx-593fa798f5 (P5 polish.sh)",
 "command": "$CMD", "seed": $SEED, "elapsed_s": $EL,
 "code": {"git": "$CODE + strategies/P5 (uncommitted)", "kernel_sha256": "$KSHA"},
 "aes_check": "$OKL", "utc": "$(date -u +%FT%TZ)"}
JSON
    fi
  fi
fi
