#!/bin/bash
# qhubcheck chain 2 (after the recount): own circuit/synthetic check, then the independent LP (keys, then full scans)
cd ~/xs-campaigns/2026-11-07-sprint/qhubcheck
until [ -f recount.done ]; do sleep 10; done
echo "== circ_qhc $(date -u)" > circ_qhc.log
nice -n 10 timeout 900 python3 circ_qhc.py >> circ_qhc.log 2>&1
echo "EXIT $? $(date -u)" >> circ_qhc.log
for V in GstarN1HUBDARK GstarN1HUB2DARK GstarN1HUB2DARKPK GstarN1HUB2XDARKPK; do
  echo "== keys $V $(date -u)" >> lp_qhc_keys.log
  nice -n 10 timeout 1500 python3 lp_qhc.py keys $V >> lp_qhc_keys.log 2>&1
  echo "EXIT $? $(date -u)" >> lp_qhc_keys.log
done
touch keys.done
for V in GstarN1HUB2DARK GstarN1HUB2DARKPK; do
  echo "== scan $V $(date -u)" >> lp_qhc_scan.log
  nice -n 10 timeout 2400 python3 lp_qhc.py scan $V >> lp_qhc_scan.log 2>&1
  echo "EXIT $? $(date -u)" >> lp_qhc_scan.log
done
touch chain2.done
