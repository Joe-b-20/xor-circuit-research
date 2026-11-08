#!/bin/bash
# z_r10.sh -- start r10.sh in the background
cd ~/xs-campaigns/2026-11-07-sprint/d4c2 || exit 1
nohup setsid bash r10.sh > r10.log 2>&1 < /dev/null &
sleep 30
cat r10.log
free -m | head -2
