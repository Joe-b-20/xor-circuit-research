#!/bin/bash
# Locate inverse-MixColumns record files (g118-d5, g119, g120) per campaign.
cd ~/xs-campaigns || exit 1
for d in 2026-10-31-adopt 2026-11-03-waits 2026-11-04-12h 2026-11-05-inv-star 2026-11-05-inv118 2026-11-06-w500 2026-11-03-12h 2026-11-02-v9b 2026-11-02-v9c 2026-11-03-v9e 2026-11-06-layout 2026-10-31-long; do
  n118=$(find "$d" -name "g118-d5-*.json" 2>/dev/null | wc -l)
  n119=$(find "$d" -name "g119-*.json" 2>/dev/null | wc -l)
  n120=$(find "$d" -name "g120-*.json" 2>/dev/null | wc -l)
  echo "$d g118: $n118  g119: $n119  g120: $n120"
  find "$d" -name "g118-d5-*.json" 2>/dev/null | sed 's#/records/.*##' | sort | uniq -c | sort -rn | head -4
done
echo "--- sample record"
f=$(find 2026-11-05-inv-star -name "g118-d5-*.json" 2>/dev/null | head -1)
echo "$f"
head -c 1200 "$f"
echo
