#!/bin/bash
cd ~/xcr-boolflux/nonlinear/boolflux/strategies/H2
while systemctl --user is-active --quiet xs-H-h2all2g; do sleep 10; done
export H2_BUILDLIST=~/xs-campaigns/2026-11-15-study/H2/builds-for-T1.txt
# tier-1 slice: H4 covers, members, K = 13, all gammas; stops at 06:10 UTC
timeout $(( $(date -u -d "06:10" +%s) - $(date -u +%s) )) bash qworker.sh ~/xs-campaigns/2026-11-15-study/H2/h4-specs.txt 1 0 13 ~/xs-campaigns/2026-11-15-study/H2/t1a-now 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15
