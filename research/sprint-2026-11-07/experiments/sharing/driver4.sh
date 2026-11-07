#!/bin/bash
# Deeper closure-deficiency runs (replaces driver3.sh), most valuable first, after cone_core(25).
cd ~/xs-campaigns/2026-11-07-sprint/sharing || exit 1
until grep -q "cone_core(25) done" driver.log; do sleep 10; done
P="nice -n 8 python3"
run () {  # K e_max limit
  timeout "$3" $P closure_dfs.py "$1" "$2" >> closure.log 2>&1 || echo "{\"K\": \"$1\", \"e_max\": $2, \"result\": \"timeout\", \"limit\": $3}" >> closure.log
}
run 6,7 4 120
run 0,1 4 120
run 1,3 3 120
run 1,4 3 120
run 5,6 4 120
run 0,7 4 120
echo "closure stage A done $(date -u +%FT%TZ)" >> driver.log
for K in 3,4 0,3 1,2 2,3 4,5 1,7 0,4 3,7 4,7; do run $K 4 100; done
echo "closure stage B done $(date -u +%FT%TZ)" >> driver.log
run 6,7 5 300
run 0,1 5 300
run 1,3 4 200
run 1,4 4 200
echo "closure stage C done $(date -u +%FT%TZ)" >> driver.log
run 6,7 6 400
run 0,1 6 400
echo "closure2 done $(date -u +%FT%TZ)" >> driver.log
