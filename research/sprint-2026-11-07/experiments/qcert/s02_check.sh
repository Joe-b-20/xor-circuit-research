#!/bin/bash
cd ~/xs-campaigns/2026-11-07-sprint/qcert
( time nice -n 8 python3 check_ext75.py CERTIFICATES_EXT75.json ) > s02_check.out 2>&1
echo "exit $?" >> s02_check.out
cat s02_check.out
