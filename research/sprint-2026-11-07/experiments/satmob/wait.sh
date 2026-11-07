#!/bin/bash
# wait.sh PATTERN COUNT MAXSECS : block until run.log holds >= COUNT lines matching PATTERN
cd ~/xs-campaigns/2026-11-07-sprint/satmob
t0=$(date +%s)
while [ "$(grep -c "$1" run.log)" -lt "$2" ]; do
  sleep 20
  if [ $(( $(date +%s) - t0 )) -ge "$3" ]; then echo "wait expired"; break; fi
done
grep -E "TIMEOUT|run complete|!!!!!|ERROR" run.log | tail -10
date
