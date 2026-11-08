#!/bin/bash
# r7.sh -- replaces the tails of r5.sh / r6.sh.  FULLnoR2 ended at bound 30 (30 reached at 1,373 s of 1,400):
# one core short.  The no-two-helper scope splits as B0noR2 (closed in d4c) u BJnoR2 u MnoR2, so its two open
# parts go first as separate pure minimisations (each needs 31 on a smaller branch); then the two families with
# two-helper recipes, BJ and M.  Solver limits are cut so that the queue ends before ~05:50 UTC.
cd ~/xs-campaigns/2026-11-07-sprint/d4c2 || exit 1
export PYTHONDONTWRITEBYTECODE=1
while pgrep -f "[b]ash r5.sh" > /dev/null || pgrep -f "[b]ash r6.sh" > /dev/null || pgrep -f "[e]3_run.py" > /dev/null; do sleep 3; done
TM=/usr/bin/time
END=$(date -u -d "05:50" +%s)
run () {
  if [ -e STOP7 ]; then echo "STOP7 file present, skipping $1"; return; fi
  NOW=$(date -u +%s); LIM=$(( END - NOW - 60 )); [ $LIM -gt 1400 ] && LIM=1400
  if [ $LIM -lt 240 ]; then echo "skip $1 (limit $LIM s)"; return; fi
  echo "START $1 $(date -u) limit $LIM"
  nice -n 8 timeout 1500 $TM -f "MAXRSS_KB %M ELAPSED %e" python3 e3_run.py "$@" time=$LIM 2>&1 | tee "e3_$1.out"
  echo "EXIT $1 ${PIPESTATUS[0]} $(date -u)"
}
C="core=1 workers=4 sub=core4 stop=31"
run BJnoR2 fix3=W5 jmin=1 hmin=6 pc5=16 noR2=1 $C
run MnoR2 m5min=1 hmin=6 pc5=16 noR2=1 $C
run BJ fix3=W5 jmin=1 hmin=6 pc5=16 $C
run M m5min=1 hmin=6 pc5=16 $C
echo "QUEUE DONE $(date -u)"
