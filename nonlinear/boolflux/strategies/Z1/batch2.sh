#!/bin/bash
# Z1 batch 2 (CPU 1, after batch 1): the (m_1, waste) = (17, 3) route in the AD4 family:
# AD4 level-1 span + the file's OWN 6-AND middle (E = 15) + K = 12 members = 27 ANDs.
# H2 ran this middle only at K = 13 gamma 1 (control); K = 12 with the 6-AND middle was never run.
Z1=~/xcr-boolflux/nonlinear/boolflux/strategies/Z1
while systemctl --user is-active -q xs-Z-batch1; do sleep 20; done
N=/home/joebachir20/xcr-boolflux/nonlinear/nist/aes-sbox
F131=$N/aes-sbox-a28-ad4-g131-gd31-xx103-43.circ.txt
F141=$N/aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt
F176=$N/aes-sbox-a28-ad4-g176-gd14-xx148-25.circ.txt
# control: own structure (9 + 6 + 13) must be found
bash $Z1/g13case.sh m6-131-g1 file:$F131 1 13 g midfile:$F131
for g in 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
  bash $Z1/g13case.sh m6-131-g$g file:$F131 $g 12 g midfile:$F131
  bash $Z1/g13case.sh m6-141-g$g file:$F141 $g 12 g midfile:$F141
  bash $Z1/g13case.sh m6-176-g$g file:$F176 $g 12 g midfile:$F176
done
echo "batch2 done $(date -u)" >> ~/xs-campaigns/2026-11-15-targets/Z1/runs/g13/cases.log
