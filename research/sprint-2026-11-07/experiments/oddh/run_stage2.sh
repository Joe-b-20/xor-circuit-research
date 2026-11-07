#!/bin/bash
# h=3 sub-domain enumeration (C++), then the single-helper d-table (python); one process at a time.
D=~/xs-campaigns/2026-11-07-sprint/oddh
cd "$D/run"
echo "=== h3_rank start $(date -u +%H:%M:%S)"
/usr/bin/time -f "h3_rank: wall %es user %Us maxrss %MKB" nice -n 8 ./h3_rank D1 D4 D2 D3 > h3_rank.json 2> h3_rank.stderr
cat h3_rank.json; cat h3_rank.stderr
echo "=== h1tab start $(date -u +%H:%M:%S)"
cd "$D"
/usr/bin/time -f "h1tab: wall %es maxrss %MKB" nice -n 8 python3 indep.py h1tab > run/indep_h1tab.log 2>&1
cat run/indep_h1tab.log
echo "=== done $(date -u +%H:%M:%S)"
