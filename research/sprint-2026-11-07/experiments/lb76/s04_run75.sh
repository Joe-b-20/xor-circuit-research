#!/bin/bash
# Run the package's LP model (lp_regen.py, unchanged) at G=75 and G=76 via g75_survivors.py.
cd ~/xs-campaigns/2026-11-07-sprint/lb76 || exit 1
echo "start $(date -u +%FT%TZ)" > g75_run.log
timeout 1500 nice -n 10 python3 g75_survivors.py 75 76 >> g75_run.log 2>&1
echo "exit $?" >> g75_run.log
echo "end $(date -u +%FT%TZ)" >> g75_run.log
cat g75_run.log
