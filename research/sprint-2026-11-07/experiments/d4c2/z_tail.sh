#!/bin/bash
# z_tail.sh TAG [N] -- last N lines of a solver log (excluding the long parameter line)
cd ~/xs-campaigns/2026-11-07-sprint/d4c2 || exit 1
grep -v '^Parameters' "e3_$1.log" | tail -${2:-30} | cut -c1-200
