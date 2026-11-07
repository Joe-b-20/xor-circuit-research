#!/bin/bash
cd ~/xs-campaigns/2026-11-07-sprint/qreal
timeout 600 nice -n 8 python3 -u fullmet.py M,Mt 2>&1 | tee fullmet.log
bash run_geo.sh
