#!/bin/bash
# X2 A/B arm (foreground; run inside an xsrun unit, see ab.sh): copy the snapshot, write control.json, run
# the generic or the goal scheduler.
#   arm.sh KIND(generic|goal) NAME HOURS CPUS SEED [extra scheduler args...]
set -e
KIND=$1; NAME=$2; HOURS=$3; CPUS=$4; SEED=$5; shift 5
BASE=/home/joebachir20/xs-campaigns/2026-11-15-study/X2
SNAP=$BASE/snap0
D=$BASE/$NAME
HUB=/home/joebachir20/xcr-boolflux/nonlinear/boolflux/hub
if [ -e $D ]; then echo "exists: $D"; exit 1; fi
cp -a $SNAP $D
# same configuration as long3/long4 (strategies/E/NOTES.md "long3 final"): nursery 0.3, ad3_share 0.3; no ingest
cat > $D/control.json <<EOF
{"ops": ["polish", "pull", "join", "trb", "osc", "gen_skel"], "nursery": 0.3, "ad3_share": 0.3,
 "note": "X2 A/B arm $NAME ($KIND)"}
EOF
if [ $KIND = generic ]; then S=$HUB/scheduler.py; else S=$HUB/scheduler_goal.py; fi
cd /home/joebachir20/xcr-boolflux
echo "$(date -u +%FT%TZ) start $KIND $NAME hours $HOURS cpus $CPUS seed $SEED" | tee -a $BASE/ab.log
python3 $S --dir $D --cpus $CPUS --hours $HOURS --seed $SEED --nursery 0.3 --ops polish,pull,join,trb,osc,gen_skel "$@" > $D/hub.log 2>&1 || echo "$(date -u +%FT%TZ) $NAME exit $?" | tee -a $BASE/ab.log
echo "$(date -u +%FT%TZ) end $NAME" | tee -a $BASE/ab.log
