#!/bin/bash
# Run one python step detached from the wsl.exe shell (one python process at a time, nice 10).
# Usage: run_bg.sh SCRIPT.py
cd ~/xs-campaigns/2026-11-07-sprint/invtransfer || exit 1
name="${1%.py}"
setsid nohup nice -n 10 python3 "$1" > "$name.log" 2>&1 < /dev/null &
disown
sleep 2
echo "launched $1 pid $! ; log $name.log"
ps aux | grep "[p]ython3 $1" | head -2
