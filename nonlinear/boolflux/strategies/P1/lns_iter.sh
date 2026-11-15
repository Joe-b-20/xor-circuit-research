#!/bin/bash
# P1: iterated unionsat2 LNS on one CPU: R rounds of S seconds; each round restarts from the previous
# round's best circuit (if it improved) or its final walked circuit, so the pool (archive span +
# DATA/shared, refreshed by lnsharvest between rounds) and the rotation closure are rebuilt around the
# current point.  Usage: lns_iter.sh NAME D CAP_AD START ROUNDS SECONDS SEED [extra unionsat2 args]
set -u
name=$1; D=$2; cad=$3; start=$4; R=$5; S=$6; seed=$7; shift 7
P1=/home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P1
D0=/home/joebachir20/xs-campaigns/2026-11-15-targets/P1
mkdir -p $D0/runs/iter/$name; cd $D0/runs/iter/$name
cur=$start
for r in $(seq 1 $R); do
  echo "== $(date -u +%H:%M:%S) round $r start $cur seed $seed"
  python3 $P1/unionsat2.py --lns $cur --starts $D0/starts_fam.json --extra $D0/shared --D $D --cap-ad $cad \
    --seconds $S --lns-sec 20 --seed $seed --out r$r-best.circ.txt --outdir r$r-out --final r$r-final.circ.txt \
    --log $D0/runs/iter/iter.jsonl "$@" > r$r.log 2>&1
  tail -1 r$r.log | cut -c1-300
  if [ -f r$r-best.circ.txt ]; then cur=$PWD/r$r-best.circ.txt; elif [ -f r$r-final.circ.txt ]; then cur=$PWD/r$r-final.circ.txt; fi
  python3 $P1/lnsharvest.py $D0 $D0/runs/iter/$name 2>&1 | tail -2
  seed=$((seed + 1))
done
echo "== $(date -u +%H:%M:%S) done"
