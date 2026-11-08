#!/bin/bash
# r4.sh -- follows r3.sh (which is told by STOP3 to end after B0).  The remaining families of the case split
# of scope C, each as ONE pure core minimisation (full objective, no cardinality fixed, stop at 31):
#   BJ  = m = 0 (all weight-5 outputs at level 3) and j >= 1 realisable weight-7 outputs at level 3
#   M   = m >= 1 (some weight-5 output at level 4), j free
# B0 (m = 0, j = 0) u BJ u M = scope C.  Then the full scope without two-helper recipes (d4c's FULLnoR2b).
cd ~/xs-campaigns/2026-11-07-sprint/d4c2 || exit 1
export PYTHONDONTWRITEBYTECODE=1
while pgrep -f "[b]ash r3.sh" > /dev/null || pgrep -f "[e]3_run.py" > /dev/null; do sleep 3; done
sed -i 's/\r$//' e2_model.py e3_run.py e5_verify.py
TM=/usr/bin/time
run () {
  if [ -e STOP4 ]; then echo "STOP4 file present, skipping $1"; return; fi
  echo "START $1 $(date -u)"
  nice -n 8 timeout 1500 $TM -f "MAXRSS_KB %M ELAPSED %e" python3 e3_run.py "$@" 2>&1 | tee "e3_$1.out"
  echo "EXIT $1 ${PIPESTATUS[0]} $(date -u)"
}
C="core=1 workers=4 sub=core4 time=1400 stop=31"
run BJ fix3=W5 jmin=1 hmin=6 pc5=16 $C
run M m5min=1 hmin=6 pc5=16 $C
run FULLnoR2 hmin=6 pc5=16 noR2=1 $C
echo "QUEUE DONE $(date -u)"
