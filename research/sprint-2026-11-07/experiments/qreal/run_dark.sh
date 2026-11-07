#!/bin/bash
cd ~/xs-campaigns/2026-11-07-sprint/qreal
timeout 1700 nice -n 8 python3 -u qr_lp.py scan GstarN1HUBDARKM 75 2>&1 | tee scan_dark.log
