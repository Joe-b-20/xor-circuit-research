#!/bin/bash
# P1: sequence of unionsat2 (span-pooled) LNS runs on one CPU.  LIST lines: name D start seconds cap_ad
# Logs ~/xs-campaigns/2026-11-15-targets/P1/runs/usat2/<name>.log, best <name>-best.circ.txt,
# improved / sideways circuits <name>-out/.  Pool = every survey circuit in the start's span + DATA/shared.
set -u
P1=/home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P1
D0=/home/joebachir20/xs-campaigns/2026-11-15-targets/P1
mkdir -p $D0/runs/usat2; cd $D0/runs/usat2
seed=${SEED:-21}
LIST=${LIST:-$P1/lns2_list1.txt}
while read -r name D start sec cad; do
  [ -z "$name" ] && continue
  case "$name" in \#*) continue;; esac
  echo "== $(date -u +%H:%M:%S) $name D $D start $start sec $sec cap_ad $cad seed $seed"
  python3 $P1/unionsat2.py --lns $start --starts $D0/starts_fam.json --extra $D0/shared --D $D --cap-ad $cad \
    --seconds $sec --lns-sec 20 --seed $seed --out $name-best.circ.txt --outdir $name-out \
    --log $D0/runs/usat2/lns2.jsonl > $name.log 2>&1
  tail -1 $name.log | cut -c1-400
  seed=$((seed + 1))
done < $LIST
echo "== $(date -u +%H:%M:%S) done"
