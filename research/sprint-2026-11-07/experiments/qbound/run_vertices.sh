#!/bin/bash
# vertex solutions of the local LP (G* variant) for representative LP-feasible keys at G=75
cd ~/xs-campaigns/2026-11-07-sprint/qbound
for k in "14 3 3 1 1 Mt" "13 4 4 1 2 Mt" "12 5 5 1 3 Mt" "16 1 1 1 1 Mt" "11 5 5 5 0 Mt" "13 4 4 3 2 M" "12 5 5 2 3 M" "10 6 6 6 0 M" "17 2 2 4 1 M"; do
  nice -n 12 python3 qb_lp.py vertex $k Gstar 2>&1 | head -20
done
