#!/bin/bash
# usage: bash xcheck_sat.sh [long]    independent SAT cross-checks of exhaustive-search results (sat2.py)
# "long" adds a 13-gate UNSAT question for 1|2|03|12 (no answer within 300 s on 2026-11-11).
cd "$(dirname "$0")"
ulimit -v 8000000
{
echo "== 12|03|013|012 : expect UNSAT at 12, SAT at 13"
timeout 300 python3 sat2.py '12|03|013|012' 12 13 | grep -E 'k=|L =|no circuit'
echo "== 12|03|013|012 restricted to pair-partition circuits: expect UNSAT at 13"
timeout 300 python3 sat2.py '12|03|013|012' 13 13 --pair | grep -E 'k=|L =|no circuit'
if [ "$1" = "long" ]; then
  echo "== 1|2|03|12 (delta = 1, delta(T^T) = 2): expect UNSAT at 13"
  timeout 300 python3 sat2.py '1|2|03|12' 13 13 | grep -E 'k=|L =|no circuit'
fi
echo "== end"
} > xcheck_sat.txt 2>&1
