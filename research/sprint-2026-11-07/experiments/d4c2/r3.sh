#!/bin/bash
# r3.sh -- replaces r2.sh.  Fixing a cardinality (|L2| = 24 in K24, |H3| = 6 in H6) made every SAT call of the
# core loop a hard feasibility search (K24 sat at its propagation bound 30 for 456 s, H6 at 16 for ~280 s), so
# back to the protocol that climbed in d4c: pure core minimisation of the full objective |L2| + |H3| with no
# cardinality fixed, stop at 31.  Order: the 89's level pattern B0 with two-helper recipes (covers every
# k = |L2|, in particular k = 24, 23), then the full scope without two-helper recipes, then the J / m families.
cd ~/xs-campaigns/2026-11-07-sprint/d4c2 || exit 1
export PYTHONDONTWRITEBYTECODE=1
while pgrep -f "[e]3_run.py" > /dev/null; do sleep 3; done
sed -i 's/\r$//' e2_model.py e3_run.py e5_verify.py
TM=/usr/bin/time
run () {
  if [ -e STOP3 ]; then echo "STOP3 file present, skipping $1"; return; fi
  echo "START $1 $(date -u)"
  nice -n 8 timeout 1500 $TM -f "MAXRSS_KB %M ELAPSED %e" python3 e3_run.py "$@" 2>&1 | tee "e3_$1.out"
  echo "EXIT $1 ${PIPESTATUS[0]} $(date -u)"
}
C="core=1 workers=4 sub=core4 time=1400 stop=31"
run B0 fix3=W5 fix4=W7 hmin=6 pc5=16 $C
run FULLnoR2 hmin=6 pc5=16 noR2=1 $C
echo "QUEUE DONE $(date -u)"
