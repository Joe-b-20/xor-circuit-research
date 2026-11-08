#!/bin/bash
# z_who.sh TAG... -- which subsolver produced each bound improvement
cd ~/xs-campaigns/2026-11-07-sprint/d4c2 || exit 1
for t in "$@"; do
  echo "== $t"
  grep -E '^#Bound' "e3_$t.log" | awk '{print $5}' | sort | uniq -c
done
