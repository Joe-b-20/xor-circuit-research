#!/bin/bash
# z_r5.sh -- block r4.sh and start r5.sh in the background
cd ~/xs-campaigns/2026-11-07-sprint/d4c2 || exit 1
sed -i 's/\r$//' r5.sh
touch STOP4
nohup setsid bash r5.sh > r5.log 2>&1 < /dev/null &
sleep 1
pgrep -af "bash r[0-9].sh"
