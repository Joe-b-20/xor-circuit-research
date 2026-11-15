#!/bin/bash
# conjpipe.sh LISTFILE  -- for each start file in LISTFILE: job.sh gate cap 24 (240 s), then job.sh mix cap 21
# (360 s) from that job's best; one CPU, sequential.  Logs one summary line per stage.
P3=/home/joebachir20/xs-campaigns/2026-11-15-targets/P3
S=/home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P3
while read -r ST; do
  [ -z "$ST" ] && continue
  case "$ST" in \#*) continue;; esac
  B=$(basename $ST .circ.txt)
  T1=pipe-$B-g24; T2=pipe-$B-m21
  $S/job.sh $ST gate 24 1 240 $T1
  echo "$(date -u +%T) $T1: $(head -1 $P3/runs/$T1/record.txt 2>/dev/null | sed 's/.*= //' | cut -c1-12)"
  if [ -f $P3/runs/$T1/best.circ.txt ]; then
    cp $P3/runs/$T1/best.circ.txt $P3/runs/$T1/stage1.circ.txt
    $S/job.sh $P3/runs/$T1/stage1.circ.txt mix 21 2 360 $T2
    echo "$(date -u +%T) $T2: $(head -1 $P3/runs/$T2/record.txt 2>/dev/null | sed 's/.*= //' | cut -c1-12) pareto: $(ls $P3/runs/$T2/pareto 2>/dev/null | tr '\n' ' ')"
    if [ -f $P3/runs/$T2/best.circ.txt ]; then
      T3=pipe-$B-m19
      cp $P3/runs/$T2/best.circ.txt $P3/runs/$T2/stage2.circ.txt
      $S/job.sh $P3/runs/$T2/stage2.circ.txt mix 19 3 360 $T3
      echo "$(date -u +%T) $T3: $(head -1 $P3/runs/$T3/record.txt 2>/dev/null | sed 's/.*= //' | cut -c1-12) pareto: $(ls $P3/runs/$T3/pareto 2>/dev/null | tr '\n' ' ')"
    fi
  fi
done < "$1"
