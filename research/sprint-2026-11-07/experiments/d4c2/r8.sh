#!/bin/bash
# r8.sh -- replaces the tail of r7.sh after MnoR2 (30 at 708 s, not 31 by 1,400 s): the split of MnoR2 into
# m = 1 and m >= 2 (each a pure minimisation that must reach 31; capped at 900 s each), so that the
# no-two-helper scope can still be closed in this session; then BJ and M (two-helper recipes allowed) with the
# time left.  Limits cut to end before ~05:50 UTC.
cd ~/xs-campaigns/2026-11-07-sprint/d4c2 || exit 1
export PYTHONDONTWRITEBYTECODE=1
while pgrep -f "[b]ash r7.sh" > /dev/null || pgrep -f "[e]3_run.py" > /dev/null; do sleep 3; done
TM=/usr/bin/time
END=$(date -u -d "05:50" +%s)
run () {
  if [ -e STOP8 ]; then echo "STOP8 file present, skipping $1"; return; fi
  NOW=$(date -u +%s); LIM=$(( END - NOW - 60 )); [ $LIM -gt ${CAP:-1400} ] && LIM=${CAP:-1400}
  if [ $LIM -lt 240 ]; then echo "skip $1 (limit $LIM s)"; return; fi
  echo "START $1 $(date -u) limit $LIM"
  nice -n 8 timeout 1500 $TM -f "MAXRSS_KB %M ELAPSED %e" python3 e3_run.py "$@" time=$LIM 2>&1 | tee "e3_$1.out"
  echo "EXIT $1 ${PIPESTATUS[0]} $(date -u)"
}
C="core=1 workers=4 sub=core4 stop=31"
CAP=900 run M1noR2 m5=1 hmin=6 pc5=16 noR2=1 $C
CAP=900 run M2noR2 m5min=2 hmin=6 pc5=16 noR2=1 $C
run BJ fix3=W5 jmin=1 hmin=6 pc5=16 $C
run M m5min=1 hmin=6 pc5=16 $C
echo "QUEUE DONE $(date -u)"
