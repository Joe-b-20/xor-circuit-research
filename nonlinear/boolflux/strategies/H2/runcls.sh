#!/bin/bash
cd ~/xcr-boolflux/nonlinear/boolflux/strategies/H2
D=~/xs-campaigns/2026-11-15-study/H2/real
P=$1; K=$2
timeout 3000 ./gen13c $K 0 $P.cls < $P.img > $P.K$K.cls.gsol 2> $P.K$K.cls.gerr
python3 fastrank.py $P $P.K$K.cls.gsol >> $P.K$K.cls.gerr
