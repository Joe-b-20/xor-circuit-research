#!/bin/bash
cd ~/xs-campaigns/2026-11-07-sprint/qreal
timeout 900 nice -n 8 python3 -u fullgeo.py M 25 40000 2>&1 | tee fullgeo_M.log
timeout 900 nice -n 8 python3 -u fullgeo.py Mt 25 40000 2>&1 | tee fullgeo_Mt.log
