#!/bin/bash
# X3b: x3b_cand3.py runs; $1 FILE (absolute or relative to H2/found), $2.. DROP sets; O2, cover limit 10 s.
S=~/xcr-boolflux/nonlinear/boolflux/strategies
cd ~/xcr-boolflux/nonlinear/boolflux
F=$1; [ -f "$F" ] || F=$S/H2/found/$1
shift
for w in "$@"; do
  python3 $S/X3/x3b_cand3.py $F $w O2 10 2>&1 | tee -a ~/xs-campaigns/2026-11-15-study/X3/x3b/cand3.log
done
