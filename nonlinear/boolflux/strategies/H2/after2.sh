#!/bin/bash
cd ~/xcr-boolflux/nonlinear/boolflux/strategies/H2
D=~/xs-campaigns/2026-11-15-study/H2/d13
while systemctl --user is-active --quiet xs-H-h2rb1b || systemctl --user is-active --quiet xs-H-h2after1; do sleep 10; done
./rbatch.sh $D/list3.txt 0 1 4 5 6 7
