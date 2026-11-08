#!/bin/bash
# r_q7.sh -- after r_q6: the "no two-helper recipe" sub-scope (small helper universe), 89's pattern and full.
cd ~/xs-campaigns/2026-11-07-sprint/d4c || exit 1
while pgrep -f "[r]_q6.sh" > /dev/null; do sleep 5; done
sed -i 's/\r$//' c2_model.py c3_run.py
run () {
  echo "START $1 $(date -u)"
  nice -n 8 timeout 1300 python3 c3_run.py "$@" 2>&1 | tee "c3_$1.out"
  echo "EXIT $1 $? $(date -u)"
}
run B0noR2 fix3=W5 fix4=W7 ub=30 hmin=6 noR2=1 time=300 core=1
run FULLnoR2 ub=30 hmin=6 pc5=16 noR2=1 time=300 core=1
