#!/bin/bash
# r10.sh -- M (m >= 1, two-helper recipes allowed) with 4 workers grew to 6.4 GB RSS in 257 s (bound 12) with
# under 3 GB of the machine left, and was interrupted for memory safety.  Rerun with 2 core workers (core_b,
# core_e of mix 2) and a memory watchdog (SIGINT when MemAvailable < 2 GB), limit cut to end before ~05:50 UTC.
cd ~/xs-campaigns/2026-11-07-sprint/d4c2 || exit 1
export PYTHONDONTWRITEBYTECODE=1
while pgrep -f "[b]ash r9.sh" > /dev/null || pgrep -f "[e]3_run.py" > /dev/null; do sleep 3; done
TM=/usr/bin/time
END=$(date -u -d "05:50" +%s); NOW=$(date -u +%s); LIM=$(( END - NOW - 60 )); [ $LIM -gt 1400 ] && LIM=1400
[ $LIM -lt 240 ] && { echo "skip Mw2 (limit $LIM s)"; exit 0; }
echo "START Mw2 $(date -u) limit $LIM"
( while sleep 10; do
    p=$(pgrep -f "^python3 e3_run.py Mw2 ")
    [ -z "$p" ] && break
    av=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo)
    if [ "$av" -lt 2000 ]; then echo "WATCHDOG: MemAvailable ${av} MB, SIGINT $p $(date -u)"; kill -INT $p; break; fi
  done ) &
nice -n 8 timeout 1500 $TM -f "MAXRSS_KB %M ELAPSED %e" python3 e3_run.py Mw2 m5min=1 hmin=6 pc5=16 core=1 \
  workers=2 sub=core4 stop=31 time=$LIM 2>&1 | tee e3_Mw2.out
echo "EXIT Mw2 ${PIPESTATUS[0]} $(date -u)"
wait
