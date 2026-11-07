#!/bin/bash
cd ~/xs-campaigns/2026-11-07-sprint/qreal
timeout 1500 nice -n 8 python3 -u fullgeo.py M 90 300000 2>&1 | grep -v -i warning | tee fullgeo_M.log
timeout 1500 nice -n 8 python3 -u fullgeo.py Mt 90 300000 2>&1 | grep -v -i warning | tee fullgeo_Mt.log
bash run_scans.sh GstarN1HUBDARKM 2>&1 | tee scan_dark.log
