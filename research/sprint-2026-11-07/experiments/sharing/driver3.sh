#!/bin/bash
# Deeper closure-deficiency runs, after the main driver and cone_core(25) have finished.
cd ~/xs-campaigns/2026-11-07-sprint/sharing || exit 1
until grep -q "cone_core(25) done" driver.log; do sleep 10; done
P="nice -n 8 python3"
for K in 3,4 0,3 1,2 2,3 4,5 1,7 0,4 3,7 4,7; do
  timeout 240 $P closure_dfs.py $K 4 >> closure.log 2>&1 || echo "{\"K\": \"$K\", \"e_max\": 4, \"result\": \"timeout\"}" >> closure.log
done
echo "closure e<=4 (16-target pairs) done $(date -u +%FT%TZ)" >> driver.log
for E in 4 5 6; do
  for K in 6,7 0,1; do
    timeout 420 $P closure_dfs.py $K $E >> closure.log 2>&1 || echo "{\"K\": \"$K\", \"e_max\": $E, \"result\": \"timeout\"}" >> closure.log
  done
done
timeout 300 $P closure_dfs.py 5,6,7 3 >> closure.log 2>&1 || echo "{\"K\": \"5,6,7\", \"e_max\": 3, \"result\": \"timeout\"}" >> closure.log
echo "closure2 done $(date -u +%FT%TZ)" >> driver.log
for K in 1,3 1,4; do timeout 240 $P closure_dfs.py $K 3 >> closure.log 2>&1 || echo "{\"K\": \"$K\", \"e_max\": 3, \"result\": \"timeout\"}" >> closure.log; done
echo "closure3 done $(date -u +%FT%TZ)" >> driver.log
