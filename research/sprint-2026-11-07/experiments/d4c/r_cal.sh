#!/bin/bash
# r_cal.sh -- calibration on the 89's level pattern (Y3 = 20 weight-5, Y4 = 12 weight-7), strict scope.
cd ~/xs-campaigns/2026-11-07-sprint/d4c || exit 1
sed -i 's/\r$//' c2_model.py c3_run.py
echo "START $(date -u)"
nice -n 8 timeout 700 python3 c3_run.py B0core fix3=W5 fix4=W7 time=480 core=1 workers=1 2>&1 | tee c3_B0core.out
echo "EXIT B0core $? $(date -u)"
nice -n 8 timeout 700 python3 c3_run.py B0lin2 fix3=W5 fix4=W7 time=480 lin=2 workers=1 2>&1 | tee c3_B0lin2.out
echo "EXIT B0lin2 $? $(date -u)"
