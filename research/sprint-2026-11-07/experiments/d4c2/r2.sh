#!/bin/bash
# r2.sh -- replaces the tail of r1.sh after K24 stalled at its propagation bound (24 + 6 = 30).
# Split of the 89's level pattern B0 by h = |H3| instead of k = |L2|: for fixed h minimise |L2| (pure core
# minimisation over the x literals, where the cores are cover-like), closed iff bound >= 31 - h.
# h = 6 subsumes K24 (k = 24 and cost <= 30 force h = 6); h = 7 subsumes K23, etc.
# Helper universe: h = 6 -> N6 only (hmin = 6 forces all six helpers into N6); h >= 7 -> at most h - 6
# helpers outside N6.  One process at a time, 4 core workers, nice 8, timeout 1500 s.  STOP2 ends the queue.
cd ~/xs-campaigns/2026-11-07-sprint/d4c2 || exit 1
export PYTHONDONTWRITEBYTECODE=1
while pgrep -f "[e]3_run.py" > /dev/null; do sleep 3; done
sed -i 's/\r$//' e2_model.py e3_run.py e5_verify.py
TM=/usr/bin/time
run () {
  if [ -e STOP2 ]; then echo "STOP2 file present, skipping $1"; return; fi
  echo "START $1 $(date -u)"
  nice -n 8 timeout 1500 $TM -f "MAXRSS_KB %M ELAPSED %e" python3 e3_run.py "$@" 2>&1 | tee "e3_$1.out"
  echo "EXIT $1 ${PIPESTATUS[0]} $(date -u)"
}
C="core=1 workers=4 sub=core4 time=1400 obj=x"
B0="fix3=W5 fix4=W7 hmin=6 pc5=16"
run H6 $B0 hsum=6 helpers=N6 stop=25 $C
run H7 $B0 hsum=7 outN6max=1 stop=24 $C
run H8 $B0 hsum=8 outN6max=2 stop=23 $C
run H9 $B0 hsum=9 outN6max=3 stop=22 $C
run H10 $B0 hsum=10 outN6max=4 stop=21 $C
run H11 $B0 hsum=11 outN6max=5 stop=20 $C
run H12 $B0 hsum=12 outN6max=6 stop=19 $C
run H13 $B0 hsum=13 outN6max=7 stop=18 $C
run H14 $B0 hsum=14 outN6max=8 stop=17 $C
echo "QUEUE DONE $(date -u)"
