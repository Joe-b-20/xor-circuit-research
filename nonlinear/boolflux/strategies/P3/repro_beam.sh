#!/bin/bash
# Staged pipeline with a seed beam (repair_keep 1 via job.sh): each stage runs NSEED seeds from the
# current start and passes the best (G, then GD) result on.
#   repro_beam.sh START TAG "MODE:CAP:SECS ..." SEED0 NSEED [REPRO_FILE]
ST=$1; TAG=$2; STAGES=$3; SEED=$4; NS=$5; export REPRO=${6:-}
P3=/home/joebachir20/xs-campaigns/2026-11-15-targets/P3
S=/home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P3
cur=$ST; i=0
for st in $STAGES; do
  i=$((i+1)); m=${st%%:*}; rest=${st#*:}; cap=${rest%%:*}; secs=${rest##*:}
  best=""; bkey=""
  for j in $(seq 1 $NS); do
    T=$TAG-s$i-$m$cap-k$j
    $S/job.sh $cur $m $cap $((SEED+10*i+j)) $secs $T
    r=$(head -1 $P3/runs/$T/record.txt 2>/dev/null | sed 's/.*= //' | cut -d' ' -f3,4)
    echo "$(date -u +%T) $T: ${r:-none} pareto: $(ls $P3/runs/$T/pareto 2>/dev/null | tr '\n' ' ')"
    [ -z "$r" ] && continue
    key=$(echo $r | awk '{printf "%04d%04d", $1, $2}')
    if [ -z "$bkey" ] || [ "$key" \< "$bkey" ]; then bkey=$key; best=$P3/runs/$T/best.circ.txt; fi
  done
  [ -z "$best" ] && break
  cp $best $P3/runs/$TAG-stage$i.circ.txt
  cur=$P3/runs/$TAG-stage$i.circ.txt
  echo "$(date -u +%T) $TAG stage $i -> $(basename $(dirname $best))"
done
