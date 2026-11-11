#!/bin/bash
cd ~/xor-circuit-research/research/structure-2026-11-11/review-83
ulimit -v 8000000
( timeout 120 python3 sat91.py lemma 10 > l10.log 2>&1 ) &
( timeout 900 python3 sat91.py lemma 9 --sym > l9.log 2>&1 ) &
( timeout 300 python3 sat91.py three 13 --sym > t13.log 2>&1 ) &
( timeout 1500 python3 sat91.py three 12 --sym > t12.log 2>&1 ) &
wait
echo done > run1.done
