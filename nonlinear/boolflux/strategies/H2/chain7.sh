#!/bin/bash
cd ~/xcr-boolflux/nonlinear/boolflux/strategies/H2
export H2_BUILDLIST=~/xs-campaigns/2026-11-15-study/H2/builds-for-T1.txt
timeout $(( $(date -u -d "06:12" +%s) - $(date -u +%s) )) bash ./rbatch.sh ~/xs-campaigns/2026-11-15-study/H2/d13/list3b.txt 1 6
