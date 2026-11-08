#!/bin/bash
# qhubcheck chain 3 (after chain 2): own FM tables, then the independent LP with FM rows (keys, then the final scan)
cd ~/xs-campaigns/2026-11-07-sprint/qhubcheck
until [ -f chain2.done ]; do sleep 10; done
echo "== fm_check $(date -u)" > fm_check.log
nice -n 10 timeout 900 python3 fm_check.py M,Mt >> fm_check.log 2>&1
echo "EXIT $? $(date -u)" >> fm_check.log
for V in GstarN1HUB2DARKFM GstarN1HUB2DARKPKFM; do
  echo "== keys $V $(date -u)" >> lp_qhc_keys.log
  nice -n 10 timeout 1500 python3 lp_qhc.py keys $V >> lp_qhc_keys.log 2>&1
  echo "EXIT $? $(date -u)" >> lp_qhc_keys.log
done
echo "== scan GstarN1HUB2DARKPKFM $(date -u)" >> lp_qhc_scan.log
nice -n 10 timeout 2400 python3 lp_qhc.py scan GstarN1HUB2DARKPKFM >> lp_qhc_scan.log 2>&1
echo "EXIT $? $(date -u)" >> lp_qhc_scan.log
touch chain3.done
