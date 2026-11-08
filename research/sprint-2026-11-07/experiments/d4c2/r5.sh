#!/bin/bash
# r5.sh -- replaces r4.sh (told by STOP4 to skip everything): same runs, FULLnoR2 moved first because it is the
# one most likely to close within 1,400 s (d4c: B0noR2b closed in 276 s, FULLnoR2b reached 25 in 245 s on one
# loaded core), then the two families BJ (m = 0, j >= 1) and M (m >= 1).  One process at a time.
cd ~/xs-campaigns/2026-11-07-sprint/d4c2 || exit 1
export PYTHONDONTWRITEBYTECODE=1
while pgrep -f "[b]ash r3.sh" > /dev/null || pgrep -f "[b]ash r4.sh" > /dev/null || pgrep -f "[e]3_run.py" > /dev/null; do sleep 3; done
sed -i 's/\r$//' e2_model.py e3_run.py e5_verify.py
TM=/usr/bin/time
run () {
  if [ -e STOP5 ]; then echo "STOP5 file present, skipping $1"; return; fi
  echo "START $1 $(date -u)"
  nice -n 8 timeout 1500 $TM -f "MAXRSS_KB %M ELAPSED %e" python3 e3_run.py "$@" 2>&1 | tee "e3_$1.out"
  echo "EXIT $1 ${PIPESTATUS[0]} $(date -u)"
}
C="core=1 workers=4 sub=core4 time=1400 stop=31"
run FULLnoR2 hmin=6 pc5=16 noR2=1 $C
run BJ fix3=W5 jmin=1 hmin=6 pc5=16 $C
run M m5min=1 hmin=6 pc5=16 $C
echo "QUEUE DONE $(date -u)"
