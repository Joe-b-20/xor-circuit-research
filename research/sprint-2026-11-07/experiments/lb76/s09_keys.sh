#!/bin/bash
# Record LP-feasible local keys at G=75 (package LP model, unchanged), under nice, with a timeout.
cd ~/xs-campaigns/2026-11-07-sprint/lb76 || exit 1
echo "start $(date -u +%FT%TZ)" > g75_keys.log
timeout 900 nice -n 10 python3 g75_keys.py 75 >> g75_keys.log 2>&1
echo "exit $?" >> g75_keys.log
echo "end $(date -u +%FT%TZ)" >> g75_keys.log
cat g75_keys.log
