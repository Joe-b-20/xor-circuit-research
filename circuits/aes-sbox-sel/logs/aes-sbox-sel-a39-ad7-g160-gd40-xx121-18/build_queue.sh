#!/bin/bash
# G4 stage 1 worker: build_queue.sh LIST K N  -> runs lines i with i % N == K of LIST (selbuild, one CPU)
G=$HOME/xs-campaigns/2026-11-17-push/G4
export BOOLFLUX_CACHE=$G/cache
cd $G/snap
D=$G/runs/build
mkdir -p $D
i=0
while IFS='|' read src t b tn rn sd tag; do
  [ -z "$src" ] && continue
  if (( i % $3 == $2 )); then
    if [ ! -f $D/$tag/result.json ]; then
      echo "$(date -u +%T) start $tag"
      python3 search/nonlinear/boolflux/ops/selbuild.py --in $src --top $tn --runs $rn --seed $sd \
        --top-mode $t --bottom-mode $b --out $D/$tag > $D/$tag.log 2>&1
      echo "$(date -u +%T) done $tag rc $?"
    fi
  fi
  i=$((i + 1))
done < $1
echo "$(date -u +%T) queue $2 finished"
