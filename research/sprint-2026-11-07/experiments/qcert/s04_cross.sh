#!/bin/bash
cd ~/xs-campaigns/2026-11-07-sprint/qcert
echo "=== s03.out (from mutation tests on)"
awk '/== mutation tests/{f=1} f' s03.out
echo "=== mutate_test.json"
cat mutate_test.json
echo "=== crosscheck"
( time nice -n 8 python3 crosscheck.py ) > s04_cross.out 2>&1; echo "exit $?" >> s04_cross.out
cat s04_cross.out
echo "=== stress_ext.json ranges of G* slacks (max) and tight counts"
python3 - <<'EOF'
import json
d=json.load(open('stress_ext.json'))
print('phases',d['phases'],'violations',len(d['violations']),'seconds',round(d['seconds'],1))
print('sigma_hist',d['sigma_hist'])
EOF
ls -la
