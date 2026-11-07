#!/bin/bash
# qrealcheck driver: one python process at a time, nice -n 10, everything serialized.
cd ~/xs-campaigns/2026-11-07-sprint/qrealcheck || exit 1
sed -i 's/\r$//' *.py
QREAL=~/xs-campaigns/2026-11-07-sprint/qreal
{
  for v in GstarN1HUB GstarN1HUBX GstarN1HUBXDARK; do
    timeout 1200 nice -n 10 python3 -u lp_qrc.py keys "$v" 2>&1 | grep -v -i warning
  done
} > lp_qrc_keys2.log 2>&1
echo "keys done $(date -u +%H:%M:%S)" >> progress.log
timeout 1500 nice -n 10 python3 -u circ_qrc.py 40 20 > circ_qrc.log 2>&1
echo "circ done rc=$? $(date -u +%H:%M:%S)" >> progress.log
# recount with qreal's own qr_lp.py: a verbatim copy whose only change is the OUTPUT directory (qreal/ stays read-only)
cp "$QREAL/qr_lp.py" qr_lp_recount.py
sed -i "s#OUT = Path.home()/'xs-campaigns/2026-11-07-sprint/qreal'#OUT = Path.home()/'xs-campaigns/2026-11-07-sprint/qrealcheck'#" qr_lp_recount.py
diff "$QREAL/qr_lp.py" qr_lp_recount.py > qr_lp_recount.diff
{
  for v in GstarN1HUB GstarN1HUBDARKM; do
    timeout 1700 nice -n 10 python3 -u qr_lp_recount.py scan "$v" 75 2>&1 | grep -v -i warning
  done
} > qr_lp_recount.log 2>&1
echo "recount done $(date -u +%H:%M:%S)" >> progress.log
# independent scans
{
  for v in GstarN1HUB GstarN1HUBDARK; do
    timeout 1700 nice -n 10 python3 -u lp_qrc.py scan "$v" 2>&1 | grep -v -i warning
  done
} > lp_qrc_scan.log 2>&1
echo "scans done $(date -u +%H:%M:%S)" >> progress.log
