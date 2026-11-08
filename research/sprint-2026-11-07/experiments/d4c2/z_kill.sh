#!/bin/bash
# z_kill.sh -- stop the d4c2 queue and its solver process
cd ~/xs-campaigns/2026-11-07-sprint/d4c2 || exit 1
pkill -f 'bash r[0-9].sh'
pkill -f 'e3_run.py'
sleep 1
ps -o pid,args -C python3 | grep e3_run | grep -v grep
echo killed
