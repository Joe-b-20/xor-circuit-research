#!/bin/bash
# r9.sh -- MnoR2 CLOSED (bound 31 at 1,175 s), so the m-split of r8.sh is not needed (r8 stopped, its M1noR2
# interrupted after a few seconds).  The no-two-helper scope is closed; the families with two-helper recipes
# BJ (m = 0, j >= 1) and M (m >= 1) run next, limits cut to end before ~05:50 UTC.
cd ~/xs-campaigns/2026-11-07-sprint/d4c2 || exit 1
export PYTHONDONTWRITEBYTECODE=1
while pgrep -f "[b]ash r8.sh" > /dev/null || pgrep -f "[e]3_run.py" > /dev/null; do sleep 3; done
TM=/usr/bin/time
END=$(date -u -d "05:50" +%s)
run () {
  NOW=$(date -u +%s); LIM=$(( END - NOW - 60 )); [ $LIM -gt ${CAP:-1400} ] && LIM=${CAP:-1400}
  if [ $LIM -lt 240 ]; then echo "skip $1 (limit $LIM s)"; return; fi
  echo "START $1 $(date -u) limit $LIM"
  nice -n 8 timeout 1500 $TM -f "MAXRSS_KB %M ELAPSED %e" python3 e3_run.py "$@" time=$LIM 2>&1 | tee "e3_$1.out"
  echo "EXIT $1 ${PIPESTATUS[0]} $(date -u)"
}
C="core=1 workers=4 sub=core4 stop=31"
CAP=1400 run BJ fix3=W5 jmin=1 hmin=6 pc5=16 $C
run M m5min=1 hmin=6 pc5=16 $C
echo "QUEUE DONE $(date -u)"
