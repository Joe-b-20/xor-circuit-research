#!/bin/bash
cd ~/xs-campaigns/2026-11-07-sprint/qreal
while pgrep -f "fullgeo.py" > /dev/null; do sleep 5; done
sed -i "s/\r$//" qr_lp.py
timeout 1700 nice -n 8 python3 -u qr_lp.py scan GstarN1HUBDARKMFM 75 2>&1 | grep -v -i warning | tee scan_final.log
for k in "11 5 5 5 0 Mt" "10 6 6 6 0 M" "12 5 5 2 3 M" "13 5 5 4 1 M" "12 4 4 5 1 Mt"; do
  timeout 120 nice -n 8 python3 qr_lp.py vertex  GstarN1HUBDARKMFM 2>&1 | grep -v -i warning | head -14
done > vertices_final.log 2>&1
