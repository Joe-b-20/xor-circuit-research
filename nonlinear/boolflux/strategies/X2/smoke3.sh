#!/bin/bash
set -e
D=/home/joebachir20/xs-campaigns/2026-11-15-study/X2/smoke3
cp -a /home/joebachir20/xs-campaigns/2026-11-15-study/X2/snap0 $D
echo '{"ops": ["polish", "pull", "join", "trb", "osc", "gen_skel"], "goal_ops": {"B": ["gjoin", "pull", "polish"], "D": ["gjoin", "gpull"]}}' > $D/control.json
cd /home/joebachir20/xcr-boolflux
taskset -c 11 python3 nonlinear/boolflux/hub/scheduler_goal.py --dir $D --cpus 11 --hours 0.025 --seed 3 --seconds polish=10,pull=10,gpull=10,gjoin=15 --goal-share A=0,B=0.5,C=0,D=0.5,E=0,F=0,G=0 --generic-share 0 > $D/hub.log 2>&1
python3 nonlinear/boolflux/strategies/X2/runs_table.py $D
cat $D/hub.log | tail -5
