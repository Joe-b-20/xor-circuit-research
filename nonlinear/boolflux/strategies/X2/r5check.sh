#!/bin/bash
# X2: real-length check of the goal scheduler on the review5 code (overlay X2/r5tree), on a weak 30-seed archive
# so that goal-progress events can fire within minutes.  r5check.sh NAME HOURS CPU
set -e
NAME=$1; H=$2; CPU=$3
X=/home/joebachir20/xs-campaigns/2026-11-15-study/X2
bash /home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/X2/overlay_r5.sh
D=$X/$NAME; mkdir -p $D
echo '{"ad3_share": 0.0, "keep_met": true, "note": "X2 review5 check"}' > $D/control.json
cd $X/r5tree
python3 nonlinear/boolflux/hub/scheduler_goal.py --dir $D --cpus $CPU --hours $H --seed 41 --seed-list $X/x2test.list \
  --ops pull,pull,gen_skel,gen_skel,polish,trb,join --eps 1.0 --nursery 0.5 --found $D/found > $D/hub.log 2>&1
echo "exit $?"
python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/X2/runs_table.py $D > $D/RUNS.txt
python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/X2/goal_dist_seeded.py $D > $D/GOALDIST.txt
grep -c goal-progress $D/events.jsonl || true
grep -c goal-compat-warning $D/events.jsonl || true
