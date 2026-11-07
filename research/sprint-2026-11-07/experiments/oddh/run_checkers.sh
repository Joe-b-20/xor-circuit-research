#!/bin/bash
# Run the three archive checkers one at a time under nice -n 8, timing each; outputs in run/.
D=~/xs-campaigns/2026-11-07-sprint/oddh/run
cd "$D"
for s in verify_two_helpers_primary verify_two_helpers_triangles independent_two_helper_audit; do
  echo "=== $s start $(date -u +%H:%M:%S)"
  /usr/bin/time -f "$s: wall %es user %Us maxrss %MKB exit %x" nice -n 8 "./$s" > "$s.json" 2> "$s.stderr"
  echo "exit=$?"; cat "$s.stderr"
  echo "=== $s end $(date -u +%H:%M:%S)"
done
echo ALLDONE
