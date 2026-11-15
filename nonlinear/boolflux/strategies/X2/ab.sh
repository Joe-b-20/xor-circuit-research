#!/bin/bash
# X2 A/B driver: ABBA order on one CPU, each arm HOURS from the same snapshot snap0.
#   launched as: XS_MEM=3G ~/xs-campaigns/guard/xsrun X 11 x2-ab ~/xs-campaigns/2026-11-15-study/X2/ab.out -- bash ab.sh 0.92
H=${1:-0.92}
A=/home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/X2/arm.sh
bash $A generic gen1 $H 11 9
bash $A goal    goal1 $H 11 9
bash $A goal    goal2 $H 11 11
bash $A generic gen2 $H 11 11
echo "$(date -u +%FT%TZ) ab done" >> /home/joebachir20/xs-campaigns/2026-11-15-study/X2/ab.log
