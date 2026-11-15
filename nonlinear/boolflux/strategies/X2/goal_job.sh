#!/bin/bash
# X2 overnight job: the goal-directed hub (hub/scheduler_goal.py) on L1's goal-focused seed directory (the SAME
# seed list as L1's focus/base arms, so the three arms are comparable), then L1's harvest (aes_check + sidecars)
# and L1's evaluation (eval_run.py) plus X2's goal-distance comparison (ab_compare.py).
#
#   goal_job.sh NAME CPULIST HOURS
#     NAME     directory name under ~/xs-campaigns/2026-11-15-study/X2/overnight/ (and X2/found/NAME)
#     CPULIST  e.g. 0,1,2,3,4,5 (one busy process per CPU; the scheduler pins each job itself)
#     HOURS    scheduler run length
#   env STEPS (default "seed run harvest eval"), SEEDLIST (default: L1's shared overnight seed list, built
#   from the long archive under L1's lock if it does not exist yet)
#
# Launch through the guard, e.g.
#   XS_MEM=3G ~/xs-campaigns/guard/xsrun X 0-5 x2-goal LOG -- bash goal_job.sh goal 0,1,2,3,4,5 12
# Read-only on the long archive and on L1's files.
set -u
NAME=$1; CPUS=$2; HOURS=$3
STEPS=${STEPS:-"seed run harvest eval"}
X2=/home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/X2
L=/home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/L1
SCHED=/home/joebachir20/xcr-boolflux/nonlinear/boolflux/hub/scheduler_goal.py
SRC=/home/joebachir20/xs-campaigns/2026-11-14-hub/long/archive
LB=/home/joebachir20/xs-campaigns/2026-11-15-study/L1
BASE=/home/joebachir20/xs-campaigns/2026-11-15-study/X2
D=$BASE/overnight/$NAME
FOUND=$BASE/found/$NAME
mkdir -p "$D" "$FOUND" "$LB/overnight"
echo "goal_job $NAME cpus $CPUS hours $HOURS steps [$STEPS] start $(date -u)"
cd /home/joebachir20/xcr-boolflux

SEEDARG=""
if [[ " $STEPS " == *" seed "* ]] && [ ! -d "$D/archive" ]; then
  if [ -n "${SEEDLIST:-}" ]; then cp "$SEEDLIST" "$D/seed.list"
  else
    SL=$LB/overnight/seed.list
    ( flock 9; [ -s "$SL" ] || python3 "$L/mk_focus_seeds.py" --src "$SRC" --out "$SL" ) 9>"$LB/overnight/.seed.lock" || exit 2
    cp "$SL" "$D/seed.list"
  fi
  SEEDARG="--seed-list $D/seed.list"
fi

if [[ " $STEPS " == *" run "* ]]; then
  # generic share (8 %) runs the original bandit-free uniform choice of L1's focus list (eps 1.0); goal jobs use
  # their own operator choice (eps 0.1, priors = L1's suggested split); ad3_share 0; nursery 0.5 (generic part)
  [ -f "$D/control.json" ] || echo '{"ad3_share": 0.0, "keep_met": true, "note": "X2 goal-directed hub, overnight"}' > "$D/control.json"
  python3 "$SCHED" --dir "$D" --cpus "$CPUS" --hours "$HOURS" --seed 31 $SEEDARG \
      --ops pull,pull,gen_skel,gen_skel,polish,trb,join --eps 1.0 --nursery 0.5 --found "$FOUND"
  echo "scheduler exit $? $(date -u)"
fi

if [[ " $STEPS " == *" harvest "* ]]; then
  python3 "$L/harvest.py" --dir "$D" --found "$FOUND" --ref "$SRC" > "$D/HARVEST.txt" 2>&1
  echo "harvest exit $? ; $(tail -1 "$D/HARVEST.txt")"
fi

if [[ " $STEPS " == *" eval "* ]]; then
  mkdir -p "$D/eval"
  ( cd "$L" && L1_OUT="$D/eval" python3 l1_load.py "$NAME=$D" && L1_OUT="$D/eval" python3 eval_run.py ) > "$D/EVAL.txt" 2>&1
  echo "eval exit $? -> $D/EVAL.txt"
  # goal distance vs the seed state (the seed records are the baseline: admitted before the first job)
  python3 "$X2/goal_dist_seeded.py" "$D" > "$D/GOALDIST.txt" 2>&1
  echo "goal distance -> $D/GOALDIST.txt"
fi
echo "goal_job $NAME done $(date -u)"
