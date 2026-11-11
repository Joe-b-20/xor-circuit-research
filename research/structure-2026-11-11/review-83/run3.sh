#!/bin/bash
cd ~/xor-circuit-research/research/structure-2026-11-11/review-83
ulimit -v 8000000
( timeout 600 python3 sat91.py three 13 --enum 400 > e13.log 2>&1 ) &
( timeout 600 python3 sat91.py three 14 --enum 400 > e14.log 2>&1 ) &
wait
python3 check_enum.py enum_three_13.json enum_three_14.json > check_enum.log 2>&1
