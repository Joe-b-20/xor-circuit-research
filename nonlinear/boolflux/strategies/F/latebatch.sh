#!/usr/bin/env bash
# all early sets x helper depth-3 targets, extras x0^x2, x1^x3 (track F)
OUT=$1; ITERS=$2; SEEDS=$3; EARLY=$4
for E in $(cat $EARLY); do
  for H in "" y1^y2^y3 y0^y2^y3 y0^y1^y3 y0^y1^y2 y0^y3 y1^y2 y0^y1 y2^y3 y0^y2,y1^y3; do
    python3 $(dirname $0)/invlate.py $OUT --early $E --extras 0^2,1^3 --force3 "$H" --seeds $SEEDS --iters $ITERS 2>/dev/null
  done
done
