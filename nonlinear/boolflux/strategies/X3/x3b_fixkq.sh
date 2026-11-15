#!/bin/bash
# X3b: stage-1-free 12 + 1 test; $1 FILE (in H2/found), $2 DROP, $3 O|O2|OV, $4 block index, $5 block log2 size
S=~/xcr-boolflux/nonlinear/boolflux/strategies
cd ~/xcr-boolflux/nonlinear/boolflux
F=$S/H2/found/$1
A=$(( $4 << $5 )); B=$(( A + (1 << $5) ))
python3 $S/X3/x3b_fixkq.py --S $F --M $F --L $F --drop $2 --O $3 --chunk $A:$B --out ~/xs-campaigns/2026-11-15-study/X3/x3b/fixkq_h2.jsonl \
  | grep -o '"drop[^]]*\]\|"O": "[A-Z0-9]*"\|"d": [0-9]*\|"chunk[^]]*\]\|"reached": [0-9]*\|"secs": [0-9.]*\|CANDIDATE' | tr '\n' ' '; echo
