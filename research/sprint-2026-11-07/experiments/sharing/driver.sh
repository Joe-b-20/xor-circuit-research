#!/bin/bash
# Sequential compute driver (one python process at a time, nice 8).
cd ~/xs-campaigns/2026-11-07-sprint/sharing || exit 1
P="nice -n 8 python3"
echo "driver start $(date -u +%FT%TZ)" > driver.log
$P cone_core.py > cone_core.log 2>&1
echo "cone_core done $(date -u +%FT%TZ)" >> driver.log
$P group_minima2.py 60 > group_minima2.log 2>&1
echo "group_minima2 done $(date -u +%FT%TZ)" >> driver.log
for K in "6,7" "0,1" "5,6" "0,7" "3,4" "0,3" "1,2" "2,3" "4,5" "1,7" "0,4" "3,7" "4,7" "0,2"; do
  timeout 300 $P closure_dfs.py "$K" 2 >> closure.log 2>&1 || echo "{\"K\": \"$K\", \"e_max\": 2, \"result\": \"timeout/err\"}" >> closure.log
done
echo "closure e<=2 done $(date -u +%FT%TZ)" >> driver.log
for K in "6,7" "0,1" "5,6,7" ; do
  timeout 600 $P closure_dfs.py "$K" 3 >> closure.log 2>&1 || echo "{\"K\": \"$K\", \"e_max\": 3, \"result\": \"timeout/err\"}" >> closure.log
done
echo "closure e<=3 done $(date -u +%FT%TZ)" >> driver.log
$P submaps.py "0,2" 120 >> submaps.log 2>&1
$P submaps.py "6,7" 600 >> submaps.log 2>&1
echo "submaps 6,7 done $(date -u +%FT%TZ)" >> driver.log
$P submaps.py "0,1" 600 >> submaps.log 2>&1
echo "submaps 0,1 done $(date -u +%FT%TZ)" >> driver.log
$P submaps.py "3,4" 600 >> submaps.log 2>&1
echo "driver end $(date -u +%FT%TZ)" >> driver.log
