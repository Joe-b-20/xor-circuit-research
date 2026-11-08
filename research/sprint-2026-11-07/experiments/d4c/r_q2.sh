#!/bin/bash
# r_q2.sh -- after c6, the full strict scope-C model, no level fixings, core-based objective, 1200 s.
cd ~/xs-campaigns/2026-11-07-sprint/d4c || exit 1
while [ ! -f c6_pc.json ]; do sleep 5; done
while pgrep -f c6_pc.py > /dev/null; do sleep 2; done
sed -i 's/\r$//' c2_model.py c3_run.py
echo "START FULL $(date -u)"
nice -n 8 timeout 900 python3 c3_run.py FULLcore time=700 core=1 workers=1 2>&1 | tee c3_FULLcore.out
echo "EXIT FULL $? $(date -u)"
