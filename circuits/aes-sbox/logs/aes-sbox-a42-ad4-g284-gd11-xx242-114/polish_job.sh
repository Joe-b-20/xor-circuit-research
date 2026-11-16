#!/bin/bash
# T4 overnight job: kernel polish of a verified AD4 GD11 circuit under hard caps, then aes_check of
# the job's best and copy into found/ with a JSON sidecar.
#   polish_job.sh START.circ.txt CAP_A MODE SEED SECONDS TAG [CAP_GD]
#   MODE: gate | osc | trb | mix (strategies/F/fdrive.py); caps GD = CAP_GD (default 11), AD 4, A = CAP_A
set -u
START=$1; CAPA=$2; MODE=$3; SEED=$4; SECS=$5; TAG=$6; CAPGD=${7:-11}
T4=<campaign archive>/2026-11-15-study/T4
OUT=$T4/queue/run-$TAG
K=<campaign archive>/2026-11-14-hub/long/bin/bfx-593fa798f5
cd <checkout>/nonlinear/boolflux
mkdir -p $OUT
env F_BFX=$K python3 strategies/F/fdrive.py --start $START --cap $CAPGD --cap-ad 4 --cap-a $CAPA \
    --mode $MODE --seconds $SECS --seed $SEED --out $OUT > $OUT/fdrive.out 2>&1
if [ -f $OUT/best.circ.txt ]; then
  python3 campaigns/aes_check.py $OUT/best.circ.txt > $OUT/aes_check.txt 2>&1
  if head -1 $OUT/aes_check.txt | grep -q '^OK'; then
    M=$(head -1 $OUT/aes_check.txt | sed 's/.*= //' | awk '{print $1"-"$2"-"$3"-"$4}')
    NAME=t4-q-$TAG-$M
    cp $OUT/best.circ.txt $T4/found/$NAME.circ.txt
    cat > $T4/found/$NAME.json <<JSON
{"file": "$NAME.circ.txt", "how": "overnight T4 polish_job: strategies/F/fdrive.py mode $MODE, caps GD$CAPGD AD4 A$CAPA, kernel bfx-593fa798f5", "start": "$START", "seed": $SEED, "seconds": $SECS, "aes_check": "$(head -1 $OUT/aes_check.txt | tr -d '\"')", "source_version": "xcr-boolflux f9fe6f7 + strategies/T4 (uncommitted)", "time": "$(date -u +%FT%TZ)"}
JSON
  fi
fi
