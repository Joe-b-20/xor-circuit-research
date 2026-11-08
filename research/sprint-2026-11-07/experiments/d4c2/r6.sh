#!/bin/bash
# r6.sh -- after r5.sh: K23 (d4c's second recommended branch, B0 with |L2| = 23, at most one helper outside N6),
# pure minimisation, solver limit chosen so that the run ends before ~05:50 UTC (and never above 1,400 s).
cd ~/xs-campaigns/2026-11-07-sprint/d4c2 || exit 1
export PYTHONDONTWRITEBYTECODE=1
while pgrep -f "[b]ash r5.sh" > /dev/null || pgrep -f "[e]3_run.py" > /dev/null; do sleep 3; done
TM=/usr/bin/time
END=$(date -u -d "05:50" +%s); NOW=$(date -u +%s)
LIM=$(( END - NOW - 60 )); [ $LIM -gt 1400 ] && LIM=1400
if [ -e STOP6 ] || [ $LIM -lt 300 ]; then echo "skip K23 (limit $LIM s)"; exit 0; fi
echo "START K23 $(date -u) limit $LIM"
nice -n 8 timeout 1500 $TM -f "MAXRSS_KB %M ELAPSED %e" python3 e3_run.py K23 fix3=W5 fix4=W7 sumx=23 hmin=6 pc5=16 \
  outN6max=1 core=1 workers=4 sub=core4 time=$LIM stop=31 2>&1 | tee e3_K23.out
echo "EXIT K23 ${PIPESTATUS[0]} $(date -u)"
