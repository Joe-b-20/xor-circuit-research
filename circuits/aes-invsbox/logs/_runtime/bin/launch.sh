#!/bin/bash
# launch.sh RUNDIR PREFIX SECONDS JOBSECONDS SCALE
#   RUNDIR      run folder (made here): RUNDIR/hub (hub archive), RUNDIR/conj (queue, jobs), RUNDIR/logs
#   PREFIX      unit name prefix, units are xs-main-PREFIX-hub and xs-main-PREFIX-c<CPU>
#   SECONDS     wall budget; every unit is hard-killed by timeout at launch + SECONDS
#   JOBSECONDS  seconds per conjugation job;  SCALE  stage-length factor of the schedules (1 = full)
# CPUs: hub 2-11 (10 workers), conjugation runners 12-19 (one unit per CPU).  CPUs 0-1 stay free.
set -e
RUN=$1; PFX=$2; SECS=$3; JOBS=$4; SCALE=${5:-1}
CAMP=$HOME/xs-campaigns/2026-11-16-invsbox
REPO=$HOME/xcr-boolflux
XSRUN=$HOME/xs-campaigns/guard/xsrun
mkdir -p "$RUN"/{hub,conj,logs}
RUN=$(cd "$RUN" && pwd)
export XS_INVSBOX=1 PYTHONPATH=$CAMP/shim
python3 $CAMP/bin/mkqueue.py --out "$RUN/conj" --seconds "$JOBS" --scale "$SCALE" > "$RUN/logs/mkqueue.log"
cp "$RUN/conj/seeds.list" "$RUN/seeds.list"
END=$(( $(date +%s) + SECS ))
HOURS=$(python3 -c "print(round(($SECS - 240) / 3600.0, 4))")
cat > "$RUN/hub/control.json" <<EOF
{"ingest": ["$RUN/conj/jobs/*/conjpull-*.circ.txt"]}
EOF
echo "$END" > "$RUN/END_EPOCH"
date -u -d @"$END" +%Y-%m-%dT%H:%M:%SZ > "$RUN/END_UTC"
cd "$REPO"
XS_MEM=3G $XSRUN main 2-11 "$PFX-hub" "$RUN/logs/hub.log" -- timeout -s TERM -k 60 "$SECS" \
  env XS_INVSBOX=1 XS_INVSBOX_LINE=1 PYTHONPATH="$CAMP/shim" python3 search/nonlinear/boolflux/hub/scheduler.py \
  --dir "$RUN/hub" --cpus 2-11 --hours "$HOURS" --seed-list "$RUN/seeds.list" --ops polish,pull,join,trb \
  --seconds polish=90,pull=90,join=60,trb=30 --eps 0.25 --seed 1
for c in $(seq 12 19); do
  XS_MEM=1G $XSRUN main "$c" "$PFX-c$c" "$RUN/logs/runner-c$c.log" -- timeout -s TERM -k 60 "$SECS" \
    env XS_INVSBOX=1 PYTHONPATH="$CAMP/shim" python3 "$CAMP/bin/runner.py" --dir "$RUN/conj" --end "$END" --name "c$c"
done
echo "launched $PFX in $RUN, hard stop $(cat "$RUN/END_UTC")"
