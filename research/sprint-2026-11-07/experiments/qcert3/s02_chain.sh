#!/bin/sh
cd ~/xs-campaigns/2026-11-07-sprint/qcert3
echo "== check_cases3 Sun Nov  8 01:07:52 UTC 2026"; nice -n 8 python3 check_cases3.py CERTIFICATES_CASES75_B3.json "{}" > s02_check.out 2>&1; echo "check EXIT 0"
echo "== fm_tab3 Sun Nov  8 01:07:52 UTC 2026"; nice -n 8 python3 fm_tab3.py > s02_fm.out 2>&1; echo "fm EXIT 0"
echo "== crosscheck3 Sun Nov  8 01:07:52 UTC 2026"; nice -n 8 python3 crosscheck3.py > s02_cross.out 2>&1; echo "cross EXIT 0"
echo "== mutate3 Sun Nov  8 01:07:52 UTC 2026"; nice -n 8 python3 mutate3.py 1 > s02_mutate.out 2>&1; echo "mutate EXIT 0"
echo "== done Sun Nov  8 01:07:52 UTC 2026"
