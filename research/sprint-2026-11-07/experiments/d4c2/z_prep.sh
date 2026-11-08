#!/bin/bash
# z_prep.sh -- strip CRs from the d4c2 scripts and syntax-check them
cd ~/xs-campaigns/2026-11-07-sprint/d4c2 || exit 1
sed -i 's/\r$//' *.py *.sh
for f in e2_model.py e3_run.py e5_verify.py; do python3 -m py_compile "$f" && echo "ok $f"; done
rm -rf __pycache__
