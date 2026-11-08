#!/bin/bash
# z_r7.sh -- block the tails of r5 / r6, start r7, interrupt the BJ run that r5 had just started (it is rerun
# by r7 after the two no-two-helper branches; its files are overwritten then)
cd ~/xs-campaigns/2026-11-07-sprint/d4c2 || exit 1
touch STOP5 STOP6
nohup setsid bash r7.sh > r7.log 2>&1 < /dev/null &
sleep 1
bash z_int.sh BJ
sleep 15
pgrep -af "bash r[0-9].sh"
pgrep -af "e3_run.py" | grep -v pgrep
tail -3 e3_BJ.out
