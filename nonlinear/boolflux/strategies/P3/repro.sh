#!/bin/bash
# Re-derivation under repair_keep 1 (compliance note 18:20): staged pipeline from a conjugate start.
#   repro.sh START TAG "MODE:CAP:SECS MODE:CAP:SECS ..." SEED0 [REPRO_FILE]
# Each stage starts from the previous stage's best.circ.txt; every job runs job.sh (pdrive with
# repair_keep 1, kernel P3/bin/bfx-4dc199db); results go to found/ with path_certified true.
ST=$1; TAG=$2; STAGES=$3; SEED=$4; export REPRO=${5:-}
P3=/home/joebachir20/xs-campaigns/2026-11-15-targets/P3
S=/home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P3
cur=$ST; i=0
for st in $STAGES; do
  i=$((i+1)); m=${st%%:*}; rest=${st#*:}; cap=${rest%%:*}; secs=${rest##*:}
  T=$TAG-s$i-$m$cap
  $S/job.sh $cur $m $cap $((SEED+i)) $secs $T
  echo "$(date -u +%T) $T: $(head -1 $P3/runs/$T/record.txt 2>/dev/null | sed 's/.*= //' | cut -c1-12) pareto: $(ls $P3/runs/$T/pareto 2>/dev/null | tr '\n' ' ')"
  [ -f $P3/runs/$T/best.circ.txt ] || break
  cp $P3/runs/$T/best.circ.txt $P3/runs/$T/stage-out.circ.txt
  cur=$P3/runs/$T/stage-out.circ.txt
done
