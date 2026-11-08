#!/bin/bash
# qhubcheck: recount of the qhub scans with a verbatim copy of qhub/qh_lp.py (only OUT changed, see qh_lp_recount.diff)
cd ~/xs-campaigns/2026-11-07-sprint/qhubcheck
for V in GstarN1HUBDARKMFM GstarN1HUB2DARKMFM GstarN1HUB2DARKMFMPK; do
  echo "== recount scan $V $(date -u)" >> qh_lp_recount.log
  nice -n 10 timeout 1500 python3 qh_lp_recount.py scan $V 75 >> qh_lp_recount.log 2>&1
  echo "EXIT $? $(date -u)" >> qh_lp_recount.log
done
touch recount.done
