#!/bin/bash
# rund13.sh NAME NEED : runs d13 on $D/NAME.txt
D=~/xs-campaigns/2026-11-15-study/H2/d13
cd ~/xcr-boolflux/nonlinear/boolflux/strategies/H2
./d13 $2 < $D/$1.txt > $D/$1.sol 2> $D/$1.err
echo "exit $?" >> $D/$1.err
