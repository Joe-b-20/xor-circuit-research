#!/bin/bash
# P2 conjugate pipeline (after P3's conjpipe idea): staged fdrive pulls from one start, saving only
# the final stage (verified, only if better than the reference start REF).
#   conjpipe.sh TARGET START REF CAPA TAG "CAP1:MODE1:SECS1 CAP2:MODE2:SECS2 ..." SEED
set -u
TGT=$1; START=$2; REF=$3; CAPA=$4; TAG=$5; STAGES=$6; SEED=$7
P2=/home/joebachir20/xs-campaigns/2026-11-15-targets/P2
K=/home/joebachir20/xs-campaigns/2026-11-14-hub/long/bin/bfx-94a75e2c18
cd /home/joebachir20/xcr-boolflux/nonlinear/boolflux
cur=$START; i=0; T0=$(date +%s); CMDS=""
for st in $STAGES; do
  i=$((i+1)); CAP=${st%%:*}; rest=${st#*:}; MODE=${rest%%:*}; SECS=${rest#*:}
  OUT=$P2/runs/$TAG-s$i; mkdir -p $OUT
  CMD="env F_BFX=$K python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P2/fdrive_p2.py --start $cur --cap $CAP --cap-ad 4 --cap-a $CAPA --mode $MODE --seconds $SECS --seed $((SEED+i)) --out $OUT"
  echo "$CMD" > $OUT/command.txt; CMDS="$CMDS ; $CMD"
  $CMD > $OUT/fdrive.out 2>&1
  [ -f $OUT/best.circ.txt ] || { echo "stage $i produced nothing" > $P2/runs/$TAG.result; exit 0; }
  cp $OUT/best.circ.txt $OUT/stage.circ.txt; cur=$OUT/stage.circ.txt
  echo "$(date -u +%T) $TAG stage $i cap $CAP $MODE: $(grep best $OUT/log.jsonl | tail -1 | cut -c1-110)" >> $P2/runs/$TAG.result
done
T1=$(date +%s)
python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P2/save.py $TGT $cur $TAG \
  --start $START --method "strategies/P2/conjpipe.sh: GF(2^8) conjugate start (P3 conj.py copy) + staged fdrive_p2 (repair_keep 1, kernel bfx-94a75e2c18) [$STAGES]" \
  --command "${CMDS# ; }" --seed $SEED --elapsed $((T1-T0)) --kernel $K --path-certified true --only-better --ref $REF >> $P2/runs/$TAG.result 2>&1
