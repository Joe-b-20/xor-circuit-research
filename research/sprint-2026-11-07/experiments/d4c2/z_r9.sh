#!/bin/bash
# z_r9.sh -- stop r8 (its m-split is redundant), interrupt its M1noR2, start r9 (BJ, M)
cd ~/xs-campaigns/2026-11-07-sprint/d4c2 || exit 1
touch STOP8
for p in $(pgrep -f "bash r8.sh"); do kill $p; done
nohup setsid bash r9.sh > r9.log 2>&1 < /dev/null &
sleep 1
bash z_int.sh M1noR2
sleep 20
pgrep -af "bash r[0-9].sh"
pgrep -af "python3 e3_run.py" | grep -v pgrep
tail -2 e3_M1noR2.out
