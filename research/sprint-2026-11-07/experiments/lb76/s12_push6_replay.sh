#!/bin/bash
# Replay the archive's push5 and push6 partial-exclusion checkers (standard library) on the copy.
cd ~/xs-campaigns/2026-11-07-sprint/lb76/push6_copy || exit 1
LOG=~/xs-campaigns/2026-11-07-sprint/lb76/push6_replay.log
echo "start $(date -u +%FT%TZ)" > "$LOG"
echo "=== push5 certify75_partial.py" >> "$LOG"
( cd push5/global_chronology && timeout 900 nice -n 10 python3 -s -E -B certify75_partial.py ) >> "$LOG" 2>&1
echo "push5 exit $?" >> "$LOG"
echo "=== push6 certify75_partial.py" >> "$LOG"
( cd push6/global_chronology && timeout 900 nice -n 10 python3 -s -E -B certify75_partial.py ) >> "$LOG" 2>&1
echo "push6 exit $?" >> "$LOG"
echo "end $(date -u +%FT%TZ)" >> "$LOG"
grep -E "start|end|exit|status|excluded_oriented|remaining_oriented|baseline_oriented|local_certificates|largest_rhs|total_oriented|Error|assert" "$LOG"
