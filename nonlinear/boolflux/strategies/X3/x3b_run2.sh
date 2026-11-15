#!/bin/bash
# X3b: H1 decomp + X3 layer tensors on NIST g124/g128, H3 g210 and X1 spangen outputs.
S=~/xcr-boolflux/nonlinear/boolflux/strategies
NI=~/xcr-boolflux/nonlinear/nist/aes-sbox
O=~/xs-campaigns/2026-11-15-study/X3/x3b
mkdir -p $O/circ
cd ~/xcr-boolflux/nonlinear/boolflux
python3 $S/X3/x3b_tocirc.py $O/circ ~/xs-campaigns/2026-11-15-study/X1/spangen1/span-*.bfx > /dev/null
G124=$NI/aes-sbox-a28-ad5-g124-gd27-xx96-26.circ.txt
G128=$NI/aes-sbox-a28-ad5-g128-gd20-xx100-27.circ.txt
H3F=~/xs-campaigns/2026-11-15-study/H3/found/h3-d2-a29-ad5-g134-gd17-7-a28-ad5-g210.circ.txt
FILES="$G124 $G128 $H3F $(ls $O/circ/*.circ.txt)"
echo "== decomp"; python3 $S/H1/decomp.py $FILES --json $O/decomp.json 2>&1 | grep -v "^ " | cut -c1-260
for f in $(ls $O/circ/*.circ.txt); do echo "== layer_tensors $(basename $f)"; python3 $S/X3/layer_tensors.py $f 2>&1 | tail -15; done
