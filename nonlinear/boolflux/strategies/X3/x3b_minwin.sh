#!/bin/bash
# X3b: minimal slack windows (k <= 5) for the three 9+5+14 files
S=~/xcr-boolflux/nonlinear/boolflux/strategies
cd ~/xcr-boolflux/nonlinear/boolflux
for F in $S/H2/found/h2-ad4a-g1-c8c7227f-s59-a28.circ.txt $S/H2/found/h2-ad4a-g1-c8c7227f-s58-a28.circ.txt \
         ~/xs-campaigns/2026-11-15-study/X1/x1b/c29/found/aes-sbox-a28-ad5-g158-gd27-x1b-span-2cabef6153f4.circ.txt; do
  python3 $S/X3/x3b_dropk.py $F 5 min | grep "top\|minimal"
done
