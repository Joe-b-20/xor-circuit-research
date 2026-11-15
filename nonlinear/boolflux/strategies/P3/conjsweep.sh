#!/bin/bash
# conjsweep.sh BASE "lam:k lam:k ..." CAPGD SECS PREFIX
# For each conjugate: mkconj.py (BP top + trb), then job.sh (pdrive gate mode, caps A32 AD4 GD CAPGD).
BASE=$1; LIST=$2; CAP=$3; SECS=$4; PFX=$5
P3=/home/joebachir20/xs-campaigns/2026-11-15-targets/P3
S=/home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P3
cd /home/joebachir20/xcr-boolflux/nonlinear/boolflux
for lk in $LIST; do
  l=${lk%%:*}; k=${lk##*:}
  ST=$P3/starts/conj-$PFX-l$l-k$k.circ.txt
  [ -f $ST ] || python3 $S/mkconj.py $BASE $l $k $ST
  TAG=$PFX-l$l-k$k-c$CAP
  echo "$(date -u +%T) start $TAG"
  $S/job.sh $ST gate $CAP 1 $SECS $TAG
  echo "$(date -u +%T) end $TAG: $(head -1 $P3/runs/$TAG/record.txt 2>/dev/null | sed 's/.*= //' | cut -c1-14) $(tail -1 $P3/runs/$TAG/record.txt 2>/dev/null | cut -c1-60)"
done
