#!/bin/bash
cd ~/xs-campaigns/2026-11-07-sprint/qjointcheck
echo "== recount scan JOINTLIM (verbatim qj_lp.py, OUT redirected)"; nice -n 10 timeout 1500 python3 qj_lp_recount.py scan GstarN1HUB2DARKPKFMJOINTLIM > recount_scan.out 2>&1; cat recount_scan.out
echo "== recount lbkeys JOINT"; nice -n 10 timeout 900 python3 qj_lp_recount.py lbkeys GstarN1HUB2DARKPKFMJOINT > recount_lb_joint.out 2>&1; tail -2 recount_lb_joint.out
echo "== recount lbkeys JOINTLIM"; nice -n 10 timeout 900 python3 qj_lp_recount.py lbkeys GstarN1HUB2DARKPKFMJOINTLIM > recount_lb_jointlim.out 2>&1; tail -2 recount_lb_jointlim.out
echo "== own rows lbkeys JC"; nice -n 10 timeout 900 python3 lp_qjc.py lbkeys GstarN1HUB2DARKPKFMJC > jc_lb_jc.out 2>&1; tail -2 jc_lb_jc.out
echo "== own rows lbkeys JCLIM"; nice -n 10 timeout 900 python3 lp_qjc.py lbkeys GstarN1HUB2DARKPKFMJCLIM > jc_lb_jclim.out 2>&1; tail -2 jc_lb_jclim.out
echo "== own rows scan JCLIM"; nice -n 10 timeout 1500 python3 lp_qjc.py scan GstarN1HUB2DARKPKFMJCLIM > jc_scan.out 2>&1; cat jc_scan.out
echo CHAIN1_DONE
