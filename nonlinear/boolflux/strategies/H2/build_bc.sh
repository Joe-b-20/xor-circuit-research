#!/bin/bash
cd ~/xcr-boolflux/nonlinear/boolflux/strategies/H2
R=~/xs-campaigns/2026-11-15-study/H2/real
export H2_BUILDLIST=~/xs-campaigns/2026-11-15-study/H2/builds-for-T1.txt
for t in ad4b ad4c; do
  timeout $(( $(date -u -d "06:35" +%s) - $(date -u +%s) )) python3 rvd.py $R/$t-g1 $R/$t-g1.K14.gsol 25 > $R/$t-g1.build.log 2>&1
done
