#!/bin/bash
cd ~/xs-campaigns/2026-11-07-sprint/qhub
until grep -q ALLDONE2 scan2.log; do sleep 5; done
echo "== circuit check rerun $(date -u)" > scan3.log
nice -n 8 timeout 600 python3 qh_circ.py > qh_circ.log 2>&1; echo "EXIT $?" >> qh_circ.log
echo "== extract $(date -u)" >> scan3.log
nice -n 8 timeout 600 python3 extract.py GstarN1HUB2DARKMFM GstarN1HUB2DARKMFMPK GstarN1HUB2LDARKMFMPK > extract.log 2>&1; echo "EXIT $?" >> extract.log
echo "ALLDONE3 $(date -u)" >> scan3.log
