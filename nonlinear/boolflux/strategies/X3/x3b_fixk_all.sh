#!/bin/bash
# X3b: complete O2 runs (2^18, 4 chunks) for both H2 9+5+14 files, unique slack-1 pair dropped.
D=~/xcr-boolflux/nonlinear/boolflux/strategies/X3
for c in 65536:131072 131072:196608 196608:262144; do
  bash $D/x3b_fixk.sh h2-ad4a-g1-c8c7227f-s59-a28.circ.txt 6,7 O2 $c | cut -c1-200
done
for c in 0:65536 65536:131072 131072:196608 196608:262144; do
  bash $D/x3b_fixk.sh h2-ad4a-g1-c8c7227f-s58-a28.circ.txt 5,6 O2 $c | cut -c1-200
done
