#!/bin/bash
# llay2all.sh JSONL SECONDS MAXRUNS : for zero-deficit lines, drop one level-1 product (cycling)
# and run track G's llay on both levels (10 + 12 slots: would be 34 ANDs at AD3)
cd "$(dirname "$0")"
D=$(dirname "$1")/llay; mkdir -p $D
n=$(wc -l < "$1"); runs=0; dj=0
for i in $(seq 0 $((n-1))); do
  sed -n "$((i+1))p" "$1" | grep -q '"deficit": 0' || continue
  pre=$D/p${i}_d$dj
  python3 ad3_llay2.py "$1" $i $pre $dj > /dev/null
  ../G/llay $pre.prob $pre $((i+1)) $2 init=$pre.init inits1=$pre.inits1 pkick=0.01
  echo "line $i drop $dj: $(tail -1 $pre.log)"
  [ -f $pre.sol ] && echo "SOLVED $pre.sol"
  dj=$(( (dj+1) % 11 )); runs=$((runs+1))
  [ $runs -ge $3 ] && break
done
