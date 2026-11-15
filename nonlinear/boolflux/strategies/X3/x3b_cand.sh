#!/bin/bash
# X3b: x3b_cand.py on an H2 file, one block; $1 FILE, $2 DROP, $3 O|O2|OV, $4 block index, $5 log2 block size
S=~/xcr-boolflux/nonlinear/boolflux/strategies
cd ~/xcr-boolflux/nonlinear/boolflux
A=$(( $4 << $5 )); B=$(( A + (1 << $5) ))
python3 $S/X3/x3b_cand.py $S/H2/found/$1 $2 $3 10 $A:$B 2>&1 | grep -v "^h2-" | tr '\n' ' ' | sed "s/^/$1 drop $2 $3 block $4: /" \
  | tee -a ~/xs-campaigns/2026-11-15-study/X3/x3b/cand.log; echo
