#!/bin/bash
# P1: sequence of unionsat LNS runs (one CPU).  Each line: name fam D K start seconds cap_ad
# Data: ~/xs-campaigns/2026-11-15-targets/P1/runs/usat/<name>.log, best -> <name>-best.circ.txt, every
# improved / sideways circuit -> <name>-out/.  Union = family members in starts_fam.json + DATA/shared.
# LIST (env) = file with the lines; default: the built-in list below.
set -u
P1=/home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P1
D0=/home/joebachir20/xs-campaigns/2026-11-15-targets/P1
cd $D0/runs/usat
seed=${SEED:-11}
LIST=${LIST:-$P1/lns_list1.txt}
while read -r name fam D K start sec cad; do
  [ -z "$name" ] && continue
  case "$name" in \#*) continue;; esac
  echo "== $(date -u +%H:%M:%S) $name fam $fam D $D K $K start $start sec $sec cap_ad $cad"
  python3 $P1/unionsat.py --fam $fam --starts $D0/starts_fam.json --extra $D0/shared --D $D --K $K --closure 1 \
    --cap-ad $cad --seconds $sec --lns $start --lns-sec 20 --seed $seed --out $name-best.circ.txt --outdir $name-out \
    --log $D0/runs/usat/lns.jsonl > $name.log 2>&1
  tail -1 $name.log
  seed=$((seed + 1))
done < $LIST
echo "== $(date -u +%H:%M:%S) done"
