#!/bin/bash
# usage: bash run_scans.sh VARIANT [VARIANT ...]   (one python process at a time, nice -n 8)
cd ~/xs-campaigns/2026-11-07-sprint/qreal
sed -i 's/\r$//' qr_lp.py
for v in "$@"; do
  timeout 1500 nice -n 8 python3 qr_lp.py scan "$v" 75 2>&1 | grep -v -i warning
done
