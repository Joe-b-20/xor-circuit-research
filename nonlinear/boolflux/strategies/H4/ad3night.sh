#!/bin/bash
# ad3night.sh OUTDIR HOURS SEED0 : unattended AD3 34-search (H4). Cycles plateau walks over
# member level-2 states (configs (k,p,l1) = (9,3,10), (8,4,10), (10,3,9), all = 34 ANDs) from
# the pool of A35-compatible states, exact level-1 cover test for every new junk space; any hit is
# built, checked with aes_check.py and saved to strategies/H4/found/ (ad3found.py).
out=$1; hours=$2; seed=$3
cd "$(dirname "$0")"
POOL=/home/joebachir20/xs-campaigns/2026-11-15-study/H4/pool_a35.jsonl
LINES=(6 9 10 11 12 13 17 18 19 20 21 22 24 25 26 28 32 35)
mkdir -p "$out"
end=$(( $(date +%s) + hours * 3600 ))
i=0
while [ $(date +%s) -lt $end ]; do
  ln=${LINES[$(( (seed + i) % ${#LINES[@]} ))]}; pool=$POOL
  case $(( i % 3 )) in
    0) args="--jmax 6 --maxl1 10";;
    1) args="--jmax 6 --maxl1 10"; pool=/home/joebachir20/xs-campaigns/2026-11-15-study/H4/ad3mem84.jsonl; ln=$(( (seed + i) % 4 ));;
    2) args="--jmax 6 --maxl1 9 --grow 1";;
  esac
  python3 ad3walk.py $pool $ln --seconds 1800 $args --seed $((seed * 1000 + i)) --out $out/walk.jsonl >> $out/walks.log 2>&1
  [ -s $out/walk.jsonl ] && python3 ad3found.py $out/walk.jsonl $out >> $out/found.log 2>&1
  i=$((i+1))
done
