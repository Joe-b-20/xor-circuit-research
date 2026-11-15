#!/bin/bash
# X3: exhaustive n=5, 3 low + 5 top (slack 0), first AND fixed to the single orbit representative (1,2);
# split over the index of the second AND (651 two-dim operand spaces), chunks of 40 (< 2 min each).
D=~/xs-campaigns/2026-11-15-study/X3; B=$D/tight
for lo in $(seq 0 40 680); do
  hi=$((lo+40))
  CLO=$lo CHI=$hi timeout 600 ~/xs-campaigns/guard/xsfg H -- taskset -c 12 $B 5 3 5 3 1 2 0 > $D/n5_L3_$lo.log 2>&1
  echo "chunk $lo done $(date -u +%H:%M:%S) $(tail -1 $D/n5_L3_$lo.log)" >> $D/n5_L3.progress
done
