#!/bin/bash
# emit new result lines of chain 2 (circuit check, LP keys, LP scans) until chain2.done exists
cd ~/xs-campaigns/2026-11-07-sprint/qhubcheck
seen=0
while true; do
  cat circ_qhc.log lp_qhc_keys.log lp_qhc_scan.log 2>/dev/null | grep -E "^A:|^B |^   |violations|variant|compared|differs|keys touched|EXIT|Traceback|Error|error" > mon_cur.txt
  n=$(wc -l < mon_cur.txt)
  if [ "$n" -gt "$seen" ]; then tail -n +$((seen+1)) mon_cur.txt; seen=$n; fi
  if [ -f chain2.done ]; then echo "CHAIN2 DONE"; exit 0; fi
  sleep 15
done
