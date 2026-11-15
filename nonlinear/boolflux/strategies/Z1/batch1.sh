#!/bin/bash
# Z1 batch 1 (CPU 1): gen13 over the two X1b 9+5 prefixes (the m_1 = 16 core), K = 13 (= 27 ANDs).
# Controls first: H2's AD4 g131 span gamma 1 K = 14 (known: covering 14-member layers exist),
# X1b prefixes K = 14 at the X1b members' gamma (7).
Z1=~/xcr-boolflux/nonlinear/boolflux/strategies/Z1
while systemctl --user is-active -q xs-Z-staircode-all; do sleep 20; done
PA=/home/joebachir20/xs-campaigns/2026-11-15-study/X1/x1b/c29/found/aes-sbox-a28-ad5-g169-gd30-x1b-span-728c49ce57b1-NU-C9.circ.txt
PB=/home/joebachir20/xs-campaigns/2026-11-15-study/X1/x1b/c29/found/aes-sbox-a28-ad5-g158-gd27-x1b-span-2cabef6153f4.circ.txt
G131=/home/joebachir20/xcr-boolflux/nonlinear/nist/aes-sbox/aes-sbox-a28-ad4-g131-gd31-xx103-43.circ.txt
bash $Z1/g13case.sh ctl-ad4a-g1 file:$G131 1 14 g
bash $Z1/g13case.sh pb-g7 file:$PB 7 14 g midfile:$PB
bash $Z1/g13case.sh pb-g7 file:$PB 7 13 g midfile:$PB
bash $Z1/g13case.sh pa-g7 file:$PA 7 14 g midfile:$PA
bash $Z1/g13case.sh pa-g7 file:$PA 7 13 g midfile:$PA
for g in 0 1 2 3 4 5 6 8 9 10 11 12 13 14 15; do
  bash $Z1/g13case.sh pb-g$g file:$PB $g 13 g midfile:$PB
  bash $Z1/g13case.sh pa-g$g file:$PA $g 13 g midfile:$PA
done
echo "batch1 done $(date -u)" >> ~/xs-campaigns/2026-11-15-targets/Z1/runs/g13/cases.log
