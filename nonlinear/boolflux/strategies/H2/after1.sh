#!/bin/bash
# wait for list1b, then validation of the 6-AND-middle option and the 9|6|12 runs
cd ~/xcr-boolflux/nonlinear/boolflux/strategies/H2
D=~/xs-campaigns/2026-11-15-study/H2/d13
while systemctl --user is-active --quiet xs-H-h2rb1b; do sleep 10; done
./rbatch.sh $D/list2v.txt 1
./rbatch.sh $D/list2a.txt 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15
