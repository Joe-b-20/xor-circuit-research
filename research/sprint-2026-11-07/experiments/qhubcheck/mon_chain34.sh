#!/bin/bash
# emit new result lines of chains 3 and 4 (FM tables, FM keys/scan, key diagnosis) until chain4.done exists
cd ~/xs-campaigns/2026-11-07-sprint/qhubcheck
until [ -f chain2.done ]; do sleep 10; done
cat lp_qhc_keys.log lp_qhc_scan.log 2>/dev/null | grep -cE "variant|compared|differs|keys touched|EXIT|Traceback|Error|error" > mon34_base.txt
base=$(cat mon34_base.txt)
seen=0
while true; do
  { cat fm_check.log vert_key.log 2>/dev/null | grep -E "full values|compared|key|case|W =|EXIT|Traceback|Error|error"; cat lp_qhc_keys.log lp_qhc_scan.log 2>/dev/null | grep -E "variant|compared|differs|keys touched|EXIT|Traceback|Error|error" | tail -n +$((base+1)); } > mon34_cur.txt
  n=$(wc -l < mon34_cur.txt)
  if [ "$n" -gt "$seen" ]; then tail -n +$((seen+1)) mon34_cur.txt; seen=$n; fi
  if [ -f chain4.done ]; then echo "CHAIN4 DONE"; exit 0; fi
  sleep 15
done
