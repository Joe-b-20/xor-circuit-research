#!/bin/bash
# wait (at most ~9.5 min) until no fullgeo.py / qr_lp.py scan process runs, then print the logs
cd ~/xs-campaigns/2026-11-07-sprint/qreal
n=0
while pgrep -f "fullgeo.py|qr_lp.py scan" > /dev/null && [ "$n" -lt 112 ]; do sleep 5; n=$((n+1)); done
echo "waited $((n*5)) s"
grep -v -i warning fullgeo_M.log | tail -2; echo ---; grep -v -i warning fullgeo_Mt.log 2>/dev/null; echo ---
grep -v -i warning scan_final.log 2>/dev/null | tail -2; echo ---; cat vertices_final.log 2>/dev/null | head -60; date
