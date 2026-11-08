#!/bin/bash
# r_q4.sh -- after r_q3: the m = 0 family with weight-7 outputs at level 3 (J != empty), then m >= 1.
cd ~/xs-campaigns/2026-11-07-sprint/d4c || exit 1
while pgrep -f "[r]_q3.sh" > /dev/null; do sleep 5; done
sed -i 's/\r$//' c2_model.py c3_run.py
run () {
  echo "START $1 $(date -u)"
  nice -n 8 timeout 1300 python3 c3_run.py "$@" 2>&1 | tee "c3_$1.out"
  echo "EXIT $1 $? $(date -u)"
}
# m = 0 (all weight-5 outputs at level 3), |J| = number of realisable weight-7 outputs at level 3
run BJ56 fix3=W5 ub=30 hmin=6 pc5=16 jmin=5 time=240 core=1
run BJ34 fix3=W5 ub=30 hmin=6 pc5=16 jmin=3 jmax=4 time=300 core=1
run BJ12 fix3=W5 ub=30 hmin=6 pc5=16 jmin=1 jmax=2 time=420 core=1
# m >= 1
run M1 m5=1 ub=30 hmin=6 pc5=16 time=420 core=1
run M2p m5min=2 ub=30 hmin=6 pc5=16 time=420 core=1
