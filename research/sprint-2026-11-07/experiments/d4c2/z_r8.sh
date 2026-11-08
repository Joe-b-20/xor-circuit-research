#!/bin/bash
# z_r8.sh -- block the tail of r7 (BJ, M) and start r8 behind it
cd ~/xs-campaigns/2026-11-07-sprint/d4c2 || exit 1
touch STOP7
nohup setsid bash r8.sh > r8.log 2>&1 < /dev/null &
sleep 1
pgrep -af "bash r[0-9].sh"
