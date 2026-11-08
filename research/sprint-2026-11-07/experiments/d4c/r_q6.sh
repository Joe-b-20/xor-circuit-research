#!/bin/bash
# r_q6.sh -- replaces r_q5 after B0k24: J >= 5 family, B0k24 as a 4-thread feasibility portfolio (900 s),
# primal lottery around the 89, then the medium branches.  One solver process at a time.
cd ~/xs-campaigns/2026-11-07-sprint/d4c || exit 1
sed -i 's/\r$//' c2_model.py c3_run.py
run () {
  echo "START $1 $(date -u)"
  nice -n 8 timeout 1300 python3 c3_run.py "$@" 2>&1 | tee "c3_$1.out"
  echo "EXIT $1 $? $(date -u)"
}
run BJ56 fix3=W5 ub=30 hmin=6 pc5=16 jmin=5 time=240 core=1
run B0k24f fix3=W5 fix4=W7 ub=30 hmin=6 sumx=24 time=900 workers=4
run LNS88 ub=30 hmin=6 pc5=16 hint=89 time=300 workers=4
run BJ34 fix3=W5 ub=30 hmin=6 pc5=16 jmin=3 jmax=4 time=300 core=1
run M1 m5=1 ub=30 hmin=6 pc5=16 time=300 core=1
