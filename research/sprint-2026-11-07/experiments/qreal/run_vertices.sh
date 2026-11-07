#!/bin/bash
cd ~/xs-campaigns/2026-11-07-sprint/qreal
V=GstarN1HUBDARKMFM
for k in "11 5 5 5 0 Mt" "10 6 6 6 0 M" "12 5 5 2 3 M" "19 0 0 1 5 Mt" "18 1 1 1 4 Mt" "7 11 4 2 6 Mt" "13 4 4 4 1 M" "12 4 4 5 1 Mt"; do
  timeout 120 nice -n 8 python3 qr_lp.py vertex $k $V 2>&1 | grep -v -i warning | grep -v "^  status" | head -9
done > vertices_final.log 2>&1
cat vertices_final.log
