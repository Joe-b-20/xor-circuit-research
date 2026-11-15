#!/bin/bash
# cpipe.sh LISTFILE: lines "START CAPAD"; per start: gate cap GD 36 (300 s), then mix cap GD 30 (400 s)
# from that best.  One CPU, sequential.  One summary line per stage.
P5=/home/joebachir20/xs-campaigns/2026-11-15-targets/P5
S=/home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P5
while read -r ST AD; do
  [ -z "$ST" ] && continue
  case "$ST" in \#*) continue;; esac
  B=$(basename $ST .circ.txt)
  T1=cp-$B-g36; T2=cp-$B-m30
  $S/cjob.sh $ST $AD 36 gate 1 300 $T1
  echo "$(date -u +%T) $T1: $(grep -c SAVED $P5/runs/$T1/record.txt) saved; best $(grep '"best"' $P5/runs/$T1/log.jsonl 2>/dev/null | tail -1 | cut -c1-90)"
  if [ -f $P5/runs/$T1/best.circ.txt ]; then
    cp $P5/runs/$T1/best.circ.txt $P5/runs/$T1/stage1.circ.txt
    $S/cjob.sh $P5/runs/$T1/stage1.circ.txt $AD 30 mix 2 400 $T2
    echo "$(date -u +%T) $T2: pareto: $(ls $P5/runs/$T2/pareto 2>/dev/null | tr '\n' ' ')"
  fi
done < "$1"
echo DONE $(date -u +%T)
