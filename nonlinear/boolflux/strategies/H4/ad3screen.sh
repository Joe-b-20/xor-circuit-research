#!/bin/bash
# ad3screen.sh K P SECONDS OUT L1FILES... : ad3fix.py on each level-1 file (one restart)
k=$1; p=$2; s=$3; out=$4; shift 4
cd "$(dirname "$0")"
i=0
for f in "$@"; do
  i=$((i+1))
  python3 ad3fix.py "$f" --k $k --p $p --seconds $s --restarts 1 --seed $i --extra ${EXTRA:-0} --out "$out" > /dev/null
done
