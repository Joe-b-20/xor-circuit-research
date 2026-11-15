#!/bin/bash
# L1 overnight job: a hub run on a goal-focused directory, then harvest (aes_check + sidecars) and evaluation.
#
#   focus_job.sh NAME CPULIST HOURS MODE
#     NAME     directory name under ~/xs-campaigns/2026-11-15-study/L1/overnight/ (and found/NAME)
#     CPULIST  e.g. 0,1,2,3,4,5 (one busy process per CPU; the scheduler pins each job itself)
#     HOURS    scheduler run length
#     MODE     focus = L1 configuration (no osc, no ad3_share, uniform operator choice with pull and
#                      gen_skel listed twice, nursery 0.5)
#              base  = the long3/long4 configuration (polish,pull,join,trb,osc,gen_skel; eps 0.25;
#                      nursery 0.3; ad3_share 0.3) on the SAME seeds, for comparison
#   env STEPS (default "seed run harvest eval"), SEEDLIST (default: built from the long hub archive)
#
# Launch through the guard, e.g.
#   XS_MEM=3G ~/xs-campaigns/guard/xsrun H 0-5 l1-focus LOG -- focus_job.sh focus 0,1,2,3,4,5 12 focus
# Uses only existing hub code (hub/scheduler.py and its operators); read-only on the long archive.
set -u
NAME=$1; CPUS=$2; HOURS=$3; MODE=$4
STEPS=${STEPS:-"seed run harvest eval"}
L=/home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/L1
SCHED=/home/joebachir20/xcr-boolflux/nonlinear/boolflux/hub/scheduler.py
SRC=/home/joebachir20/xs-campaigns/2026-11-14-hub/long/archive
BASE=/home/joebachir20/xs-campaigns/2026-11-15-study/L1
D=$BASE/overnight/$NAME
FOUND=$BASE/found/$NAME
mkdir -p "$D" "$FOUND"
echo "focus_job $NAME cpus $CPUS hours $HOURS mode $MODE steps [$STEPS] start $(date -u)"

SEEDARG=""
if [[ " $STEPS " == *" seed "* ]] && [ ! -d "$D/archive" ]; then
  if [ -n "${SEEDLIST:-}" ]; then cp "$SEEDLIST" "$D/seed.list"
  else
    # one shared list for all arms launched together (built once, under a lock), so the arms start equal
    SL=$BASE/overnight/seed.list
    ( flock 9; [ -s "$SL" ] || python3 "$L/mk_focus_seeds.py" --src "$SRC" --out "$SL" ) 9>"$BASE/overnight/.seed.lock" || exit 2
    cp "$SL" "$D/seed.list"
  fi
  SEEDARG="--seed-list $D/seed.list"
fi

if [[ " $STEPS " == *" run "* ]]; then
  if [ "$MODE" = focus ]; then
    OPS=pull,pull,gen_skel,gen_skel,polish,trb,join; EPS=1.0; NURS=0.5
    [ -f "$D/control.json" ] || echo '{"ad3_share": 0.0, "note": "L1 focus configuration"}' > "$D/control.json"
  else
    OPS=polish,pull,join,trb,osc,gen_skel; EPS=0.25; NURS=0.3
    [ -f "$D/control.json" ] || echo '{"ad3_share": 0.3, "note": "long3/long4 configuration on the L1 focus seeds"}' > "$D/control.json"
  fi
  python3 "$SCHED" --dir "$D" --cpus "$CPUS" --hours "$HOURS" --seed 21 $SEEDARG --ops "$OPS" --eps "$EPS" --nursery "$NURS"
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
fi
echo "focus_job $NAME done $(date -u)"
