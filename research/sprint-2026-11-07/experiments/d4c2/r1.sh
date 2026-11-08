#!/bin/bash
# r1.sh -- d4c2 run queue: pure core minimisation (no ub), one CP-SAT process at a time, 4 core workers,
# nice 8, timeout 1500 s per run, stop as soon as the bound reaches 31.  Order = d4c/REPORT.md section 5
# ("what would close it": k = 24, k = 23 first), then the rest of the 89's level pattern, then the
# other open families.  A file STOP in this folder ends the queue after the current run.
cd ~/xs-campaigns/2026-11-07-sprint/d4c2 || exit 1
export PYTHONDONTWRITEBYTECODE=1
sed -i 's/\r$//' e2_model.py e3_run.py e5_verify.py
TM=/usr/bin/time; [ -x $TM ] || TM=""
run () {
  if [ -e STOP ]; then echo "STOP file present, skipping $1"; return; fi
  echo "START $1 $(date -u)"
  if [ -n "$TM" ]; then
    nice -n 8 timeout 1500 $TM -f "MAXRSS_KB %M ELAPSED %e" python3 e3_run.py "$@" 2>&1 | tee "e3_$1.out"
  else
    nice -n 8 timeout 1500 python3 e3_run.py "$@" 2>&1 | tee "e3_$1.out"
  fi
  echo "EXIT $1 ${PIPESTATUS[0]} $(date -u)"
}
C="core=1 workers=4 sub=core4 stop=31 time=1400"
# B0 = the 89's level pattern (W5 at level 3, W7 at level 4)
run K24 fix3=W5 fix4=W7 sumx=24 hmin=6 helpers=N6 $C
run K23 fix3=W5 fix4=W7 sumx=23 hmin=6 outN6max=1 $C
run B0le22 fix3=W5 fix4=W7 sumxmax=22 hmin=6 pc5=16 $C
run FULLnoR2 hmin=6 pc5=16 noR2=1 $C
echo "QUEUE DONE $(date -u)"
