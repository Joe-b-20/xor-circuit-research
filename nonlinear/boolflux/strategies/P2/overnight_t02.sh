#!/bin/bash
# P2 overnight T02: independent fdrive_p2 trb seeds from the 174 (caps GD14 AD4 A28, repair_keep 1).
#   overnight_t02.sh FIRST_SEED COUNT SECS
S=/home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P2
F=/home/joebachir20/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt
for s in $(seq $1 $(($1 + $2 - 1))); do
  bash $S/polish2.sh T02 $F 28 14 trb $s ${3:-1800} on-t02-s$s
done
