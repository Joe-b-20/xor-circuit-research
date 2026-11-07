#!/bin/bash
# LP scans with the new rows, then the circuit checks (one python process at a time)
cd ~/xs-campaigns/2026-11-07-sprint/qbound
sed -i 's/\r$//' qb_lp.py circuit_check.py
for v in N1 GstarN1 GstarN1N7; do
  nice -n 12 python3 qb_lp.py scan $v 75 2>&1 | grep -v "^G=75" | tee -a scans.log
done
nice -n 12 python3 circuit_check.py 2>&1 | tee circuit_check.log
