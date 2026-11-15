#!/bin/bash
# X3b: X1b's 9+5+14 (28/5/158/27): junk, slack windows; then cand3 on windows given as args.
S=~/xcr-boolflux/nonlinear/boolflux/strategies
cd ~/xcr-boolflux/nonlinear/boolflux
F=~/xs-campaigns/2026-11-15-study/X1/x1b/c29/found/aes-sbox-a28-ad5-g158-gd27-x1b-span-2cabef6153f4.circ.txt
G124=~/xcr-boolflux/nonlinear/nist/aes-sbox/aes-sbox-a28-ad5-g124-gd27-xx96-26.circ.txt
if [ $# -eq 0 ]; then
  python3 $S/X3/x3b_junk.py $G124 $F
  python3 $S/X3/layer_tensors.py $F | tail -15
  python3 $S/X3/x3b_dropk.py $F 5 | cut -c1-400
else
  bash $S/X3/x3b_c3.sh $F "$@"
fi
