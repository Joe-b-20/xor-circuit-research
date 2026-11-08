#!/bin/bash
# r_q1.sh -- wait for the B0core calibration, skip the LP-mode calibration, then run the small exact bounds.
cd ~/xs-campaigns/2026-11-07-sprint/d4c || exit 1
while [ ! -f c3_B0core.json ]; do sleep 5; done
pkill -f r_cal.sh
sleep 2
pkill -f "c3_run.py B0lin2"
sleep 2
sed -i 's/\r$//' c2_model.py c6_pc.py
echo "START c6 $(date -u)"
nice -n 8 timeout 900 python3 c6_pc.py 2>&1 | tee c6_pc.out
echo "EXIT c6 $? $(date -u)"
