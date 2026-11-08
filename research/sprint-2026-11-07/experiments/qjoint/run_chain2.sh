#!/bin/bash
cd ~/xs-campaigns/2026-11-07-sprint/qjoint
while ! grep -q CHAIN1_DONE chain1.out; do sleep 5; done
echo "== circ" ; nice -n 8 timeout 900 python3 qj_circ.py > qj_circ.out 2>&1 ; cat qj_circ.out
echo "== scan JOINTLIM" ; nice -n 8 timeout 1200 python3 qj_lp.py scan GstarN1HUB2DARKPKFMJOINTLIM > scan_JOINTLIM.out 2>&1 ; cat scan_JOINTLIM.out
echo CHAIN2_DONE
