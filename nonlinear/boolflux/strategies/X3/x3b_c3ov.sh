#!/bin/bash
# X3b: cand3 over OV (2^24 l) for one window, one block of 2^20; $1 FILE (in H2/found), $2 DROP, $3 block 0..15
S=~/xcr-boolflux/nonlinear/boolflux/strategies
cd ~/xcr-boolflux/nonlinear/boolflux
A=$(( $3 * 1048576 )); B=$(( A + 1048576 ))
python3 $S/X3/x3b_cand3.py $S/H2/found/$1 $2 OV 10 3000000 $A:$B 2>&1 | grep -v "^D \|^h2-" | tr '\n' ' ' \
  | sed "s/^/$1 $2 OV block $3: /" | tee -a ~/xs-campaigns/2026-11-15-study/X3/x3b/cand3_ov.log; echo
