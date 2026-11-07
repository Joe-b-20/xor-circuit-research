#!/bin/bash
cd ~/xs-campaigns/2026-11-07-sprint/qhub
echo "== scan GstarN1HUB2DARKMFM Sat Nov  7 23:32:48 UTC 2026" > scan1.log
nice -n 8 timeout 1200 python3 qh_lp.py scan GstarN1HUB2DARKMFM 75 >> scan1.log 2>&1
echo "EXIT 0" >> scan1.log
echo "== reproduction scan GstarN1HUBDARKMFM Sat Nov  7 23:32:48 UTC 2026" >> scan1.log
nice -n 8 timeout 1200 python3 qh_lp.py scan GstarN1HUBDARKMFM 75 >> scan1.log 2>&1
echo "EXIT 0" >> scan1.log
echo "== hub2_check Sat Nov  7 23:32:48 UTC 2026" >> scan1.log
nice -n 8 timeout 1200 python3 hub2_check.py M,Mt > hub2_check.log 2>&1
echo "EXIT 0" >> hub2_check.log
echo "ALLDONE Sat Nov  7 23:32:48 UTC 2026" >> scan1.log
