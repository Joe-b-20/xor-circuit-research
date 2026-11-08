#!/bin/bash
cd ~/xs-campaigns/2026-11-07-sprint/qjoint
echo "== patch" ; nice -n 8 python3 patch_qj_lp.py
echo "== limit" ; nice -n 8 timeout 1200 python3 qj_limit.py M,Mt > qj_limit.out 2>&1 ; tail -12 qj_limit.out
echo "== lbkeys JOINT" ; nice -n 8 timeout 900 python3 qj_lp.py lbkeys GstarN1HUB2DARKPKFMJOINT 2>&1 | tail -3
echo "== lbkeys JOINTLIM" ; nice -n 8 timeout 900 python3 qj_lp.py lbkeys GstarN1HUB2DARKPKFMJOINTLIM 2>&1 | tail -3
echo CHAIN1_DONE
