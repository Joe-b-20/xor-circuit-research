#!/bin/bash
# Hunt E: depth-capped (cap 5) test of the depth window on MixColumns, E0 (default) vs EN (none),
# 4 workers each for 2.5 h, started when the kste1 PES run has ended (no pes2_run.py process),
# i.e. ~01:00 UTC 11-08, on the 8 threads it frees.  Sampler into samplesE/samples.jsonl.
set -u
cd "$HOME/xor-circuit-research" || exit 1
H="$HOME/xs-campaigns/2026-11-07-sprint/hunt"
log() { echo "$(date -u +%H:%M:%SZ) $*" >> "$H/driverE.log"; }
mkdir -p "$H/runsE" "$H/samplesE"
log "waiting for kste1 (pes2_run.py) to end"
while pgrep -f "pes2_run.py" > /dev/null; do sleep 60; done
sleep 30
PIDS=""
for arm in E0 EN; do
  log "starting $arm"
  python3 search/xorflux run "$H/$arm.toml" --out "$H/runsE/$arm" --set campaign.allow_oversubscription=true > "$H/$arm.run.log" 2>&1 &
  PIDS="$PIDS $!"
done
sleep 90
cd "$H"
nice -n 5 python3 sampler.py runsE samplesE/samples.jsonl 30 90 &
SP=$!
log "sampler pid $SP; runs $PIDS"
wait $PIDS
sleep 60
kill $SP 2>/dev/null
log "hunt E done"
touch "$H/E_DONE"
