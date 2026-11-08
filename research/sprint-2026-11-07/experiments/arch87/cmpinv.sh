#!/bin/bash
R=~/xs-campaigns/2026-11-07-sprint/import/zip/research/AES_OPTIMALITY_ALL_FINDINGS_COMPLETE_PUSH9_2026-10-20
A=$R/AES_OPTIMALITY_ALL_FINDINGS_2026-10-17/checkpoints/AES_FIVE_FOREIGN_AND_GLOBAL_BRIDGES_2026-10-16/canonical_00_inventory.txt
wc -l "$A"
tail -n +66 "$A" | sort > /tmp/arch87_c00.txt
for f in $R/AES_TWO_FOREIGN_2026-10-15/inventories/*; do
  tail -n +66 "$f" | sort > /tmp/arch87_x.txt
  n=$(comm -12 /tmp/arch87_c00.txt /tmp/arch87_x.txt | wc -l)
  echo "$n common helpers: $(basename $f)"
done
