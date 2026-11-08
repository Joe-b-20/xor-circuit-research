#!/bin/bash
# Run the exp1 analysis once the signature cache's final pass has exited: one process, nice 8,
# exact cataloguing capped at 1800 s (60 s per compress), up to 400 sampled hops.
E="$HOME/xs-campaigns/2026-11-07-sprint/translog/exp1"
cd "$E" || exit 1
while pgrep -f "python3 sigcache.py" > /dev/null; do sleep 5; done
echo "$(date -u +%H:%M:%SZ) analysis start" > "$E/analysis.log"
nice -n 8 python3 "$E/analyze_exp1.py" 1800 400 60 > "$E/analysis.out" 2> "$E/analysis.err"
echo "$(date -u +%H:%M:%SZ) analysis exit $?" >> "$E/analysis.log"
touch "$E/DONE_ANALYSIS"
