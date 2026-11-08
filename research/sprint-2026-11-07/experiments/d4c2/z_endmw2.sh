#!/bin/bash
# z_endmw2.sh -- end Mw2 cleanly before 05:50: stop r10's memory watchdog subshell (so that only one SIGINT is
# sent), then one SIGINT to the solver (CP-SAT stops and writes the json)
cd ~/xs-campaigns/2026-11-07-sprint/d4c2 || exit 1
for p in $(pgrep -f "bash r10.sh"); do
  if pgrep -P $p -x sleep > /dev/null; then
    s=$(pgrep -P $p -x sleep); kill $p; kill $s 2>/dev/null; echo "watchdog subshell $p stopped"
  fi
done
bash z_int.sh Mw2
sleep 25
tail -3 e3_Mw2.out | cut -c1-160
tail -2 r10.log | cut -c1-160
