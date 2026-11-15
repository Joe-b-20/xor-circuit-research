#!/bin/bash
# X3b: structure of H3's A28 (28/5/210/31) vs NIST A28-AD5 g124 / g128 and X1's spangen outputs.
S=~/xcr-boolflux/nonlinear/boolflux/strategies
NI=~/xcr-boolflux/nonlinear/nist/aes-sbox
O=~/xs-campaigns/2026-11-15-study/X3/x3b
mkdir -p $O
cd ~/xcr-boolflux/nonlinear
G124=$NI/aes-sbox-a28-ad5-g124-gd27-xx96-26.circ.txt
G128=$NI/aes-sbox-a28-ad5-g128-gd20-xx100-27.circ.txt
H3F=~/xs-campaigns/2026-11-15-study/H3/found/h3-d2-a29-ad5-g134-gd17-7-a28-ad5-g210.circ.txt
SRC=~/xs-campaigns/2026-11-14-hub/best/aes-sbox-a29-ad5-g134-gd17-xx105-51.circ.txt
SG=$(ls ~/xs-campaigns/2026-11-15-study/X1/spangen1/span-*.bfx)
echo "== x1b_family"; python3 $S/X1/x1b_family.py --ref $G124 --ref $G128 $G124 $G128 $H3F $SRC $SG 2>&1 | tail -60
for f in $G124 $G128 $H3F; do echo "== layer_tensors $(basename $f)"; python3 $S/X3/layer_tensors.py $f 2>&1 | tail -16; done
