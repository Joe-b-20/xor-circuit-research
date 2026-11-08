#!/bin/bash
# analyze the coupled-plateau circuits (core / mobile / components); output also in analyze.out
cd ~/xs-campaigns/2026-11-07-sprint/satmob2
for c in kste:3146 kste:2229 kste:1557 sampleA:109 sampleA:48 sampleA:781 sampleC:131; do
  nice -n 8 python3 mob2.py analyze "$c" 2>&1 | tail -25
done
