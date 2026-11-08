#!/bin/bash
# z_r6.sh -- start r6.sh in the background
cd ~/xs-campaigns/2026-11-07-sprint/d4c2 || exit 1
nohup setsid bash r6.sh > r6.log 2>&1 < /dev/null &
sleep 1
pgrep -af "bash r[0-9].sh"
