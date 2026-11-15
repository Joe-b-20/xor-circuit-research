#!/bin/bash
cd ~/xcr-boolflux/nonlinear/boolflux/strategies/H2
D=~/xs-campaigns/2026-11-15-study/H2/d13
while pidof gen13 > /dev/null; do sleep 10; done
bash ./rbatch.sh $D/list2v.txt 1
bash ./rbatch.sh $D/list2a.txt 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15
bash ./rbatch.sh $D/list3.txt 0 1 4 5 6 7
