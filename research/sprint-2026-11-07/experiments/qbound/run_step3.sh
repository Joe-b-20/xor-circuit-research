#!/bin/bash
# after step 2: vertex solutions of keys that survive N1, and integer feasibility of the remaining keys
cd ~/xs-campaigns/2026-11-07-sprint/qbound
sed -i 's/\r$//' qb_lp.py
for k in "14 3 3 1 1 Mt" "13 4 4 1 2 Mt" "12 5 5 1 3 Mt" "11 5 5 5 0 Mt" "10 6 6 6 0 M" "13 4 4 3 2 M" "12 5 5 2 3 M"; do
  nice -n 12 python3 qb_lp.py vertex $k GstarN1 2>&1 | head -12
done
nice -n 12 python3 qb_lp.py milp GstarN1 75 2>&1 | tail -3
