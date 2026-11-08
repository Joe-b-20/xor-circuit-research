#!/bin/bash
# qhubcheck chain 1: own H2 recomputation, then the verbatim recount of the three qhub scans (strictly sequential)
cd ~/xs-campaigns/2026-11-07-sprint/qhubcheck
echo "== h2_check $(date -u)" > h2_check.log
nice -n 10 timeout 1500 python3 h2_check.py M,Mt >> h2_check.log 2>&1
echo "EXIT $? $(date -u)" >> h2_check.log
touch h2.done
bash run_recount.sh
