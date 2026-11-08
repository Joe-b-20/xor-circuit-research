#!/bin/bash
# r_q8.sh -- replaces the tails of r_q6/r_q7: wait for the running B0k24f python, then the primal lottery,
# the two "no two-helper recipe" instances, and (time permitting) the medium branches.
cd ~/xs-campaigns/2026-11-07-sprint/d4c || exit 1
while pgrep -f "[c]3_run.py B0k24f" > /dev/null; do sleep 3; done
sed -i 's/\r$//' c2_model.py c3_run.py
run () {
  echo "START $1 $(date -u)"
  nice -n 8 timeout 1300 python3 c3_run.py "$@" 2>&1 | tee "c3_$1.out"
  echo "EXIT $1 $? $(date -u)"
}
run LNS88 ub=30 hmin=6 pc5=16 hint=89 time=300 workers=4
run B0noR2 fix3=W5 fix4=W7 ub=30 hmin=6 noR2=1 time=300 core=1
run FULLnoR2 ub=30 hmin=6 pc5=16 noR2=1 time=300 core=1
run BJ34 fix3=W5 ub=30 hmin=6 pc5=16 jmin=3 jmax=4 time=240 core=1
run M1 m5=1 ub=30 hmin=6 pc5=16 time=240 core=1
