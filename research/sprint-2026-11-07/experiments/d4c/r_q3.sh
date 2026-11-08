#!/bin/bash
# r_q3.sh -- after the full run: pattern-valid helper bounds, max-HS calibration, first |L2| = k branches
# of the 89's level pattern (Y3 = 20 weight-5, Y4 = 12 weight-7), each as a feasibility instance ub=30.
cd ~/xs-campaigns/2026-11-07-sprint/d4c || exit 1
while [ ! -f c3_FULLcore.json ]; do sleep 5; done
while pgrep -f "[c]3_run.py FULLcore" > /dev/null; do sleep 2; done
sed -i 's/\r$//' c2_model.py c3_run.py c6b_hfree.py
echo "START c6b $(date -u)"
nice -n 8 timeout 900 python3 c6b_hfree.py 2>&1 | tee c6b_hfree.out
echo "EXIT c6b $? $(date -u)"
run () {
  echo "START $1 $(date -u)"
  nice -n 8 timeout 1300 python3 c3_run.py "$@" 2>&1 | tee "c3_$1.out"
  echo "EXIT $1 $? $(date -u)"
}
run B0maxhs fix3=W5 fix4=W7 ub=30 hmin=6 time=240 maxhs=1 workers=1
run B0k16 fix3=W5 fix4=W7 ub=30 hmin=6 sumx=16 time=300 core=1
run B0k17 fix3=W5 fix4=W7 ub=30 hmin=6 sumx=17 time=300 core=1
run B0k24 fix3=W5 fix4=W7 ub=30 hmin=6 sumx=24 time=300 core=1
run B0k18 fix3=W5 fix4=W7 ub=30 hmin=6 sumx=18 time=300 core=1
run B0k23 fix3=W5 fix4=W7 ub=30 hmin=6 sumx=23 time=300 core=1
