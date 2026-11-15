#!/bin/bash
# X3b: 12 + 1 test on H2's 9+5+14 layers: drop the unique slack-1 pair, search every single product (H1 fixk.py).
# usage: x3b_fixk.sh FILE DROP O CHUNK
S=~/xcr-boolflux/nonlinear/boolflux/strategies
cd ~/xcr-boolflux/nonlinear/boolflux
F=$S/H2/found/$1
python3 $S/H1/fixk.py --S $F --M $F --L $F --drop $2 --O $3 --chunk $4 --out ~/xs-campaigns/2026-11-15-study/X3/x3b/fixk_h2.jsonl
