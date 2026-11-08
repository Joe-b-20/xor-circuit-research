#!/bin/bash
# z_bounds.sh LOG... -- print the objective-bound progress lines of CP-SAT logs
for f in "$@"; do
  echo "== $f"
  grep -E '^#(Bound|Done|Model|[0-9]+ )' "$f" | awk '{print $1, $2, $3, $4, $5, $6}' | head -80
done
