#!/bin/bash
# one python process at a time: pinned-count check, mutation tests, then the stress extension
cd ~/xs-campaigns/2026-11-07-sprint/qcert
echo "== check with pinned counts $(date -u +%H:%M:%S)" > s03.out
nice -n 8 python3 check_ext75.py >> s03.out 2>&1; echo "exit $?" >> s03.out
echo "== mutation tests $(date -u +%H:%M:%S)" >> s03.out
( time nice -n 8 python3 mutate_test.py 1 ) >> s03.out 2>&1; echo "exit $?" >> s03.out
echo "== stress_ext $(date -u +%H:%M:%S)" >> s03.out
( time nice -n 8 python3 stress_ext.py ) > stress_ext.log 2>&1; echo "stress exit $?" >> s03.out
echo "== done $(date -u +%H:%M:%S)" >> s03.out
