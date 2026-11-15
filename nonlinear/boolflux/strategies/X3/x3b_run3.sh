#!/bin/bash
# X3b: x3b_junk.py on NIST g124 (ref), g128, H3 g210, X1 spangen outputs; $1 = extra flag (--cover)
S=~/xcr-boolflux/nonlinear/boolflux/strategies
NI=~/xcr-boolflux/nonlinear/nist/aes-sbox
O=~/xs-campaigns/2026-11-15-study/X3/x3b
cd ~/xcr-boolflux/nonlinear/boolflux
G124=$NI/aes-sbox-a28-ad5-g124-gd27-xx96-26.circ.txt
G128=$NI/aes-sbox-a28-ad5-g128-gd20-xx100-27.circ.txt
H3F=~/xs-campaigns/2026-11-15-study/H3/found/h3-d2-a29-ad5-g134-gd17-7-a28-ad5-g210.circ.txt
if [ "$2" = "" ]; then FILES="$G124 $G128 $H3F $(ls $O/circ/*.circ.txt)"; else FILES="$G124 $2"; fi
python3 $S/X3/x3b_junk.py $G124 $FILES $1
