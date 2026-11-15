#!/bin/bash
# X3b: H2's 9+5+14 A28 (h2-ad4a-g1-c8c7227f-s59) vs AD4 g131 and AD5 g124.
S=~/xcr-boolflux/nonlinear/boolflux/strategies
NI=~/xcr-boolflux/nonlinear/nist/aes-sbox
cd ~/xcr-boolflux/nonlinear/boolflux
H2F=$S/H2/found/h2-ad4a-g1-c8c7227f-s59-a28.circ.txt
H2G=$S/H2/found/h2-ad4a-g1-c8c7227f-s58-a28.circ.txt
G131=$NI/aes-sbox-a28-ad4-g131-gd31-xx103-43.circ.txt
G124=$NI/aes-sbox-a28-ad5-g124-gd27-xx96-26.circ.txt
python3 campaigns/aes_check.py $H2F 2>&1 | grep -iv "published best" | head -5
echo "== junk vs g131"; python3 $S/X3/x3b_junk.py $G131 $G131 $H2F $H2G
echo "== junk vs g124"; python3 $S/X3/x3b_junk.py $G124 $H2F
echo "== tensors"; python3 $S/X3/layer_tensors.py $H2F | tail -16
