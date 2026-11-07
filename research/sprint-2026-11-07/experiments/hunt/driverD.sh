#!/bin/bash
# Hunt D: three concurrent MixColumns arms (D0 default, D4 depth_window 4, DN depth_window none),
# 4 workers each for 13 h, started when the big-map sweep is done (sweep/ALL_DONE), with a
# sampler of every chain state of at most 89 gates into samplesD/samples.jsonl.
set -u
cd "$HOME/xor-circuit-research" || exit 1
H="$HOME/xs-campaigns/2026-11-07-sprint/hunt"
log() { echo "$(date -u +%H:%M:%SZ) $*" >> "$H/driverD.log"; }
mkdir -p "$H/runsD" "$H/samplesD"
log "waiting for sweep/ALL_DONE"
while [ ! -f "$HOME/xs-campaigns/2026-11-07-sprint/sweep/ALL_DONE" ]; do sleep 30; done
sleep 20
PIDS=""
for arm in D0 D4 DN; do
  log "starting $arm"
  python3 search/xorflux run "$H/$arm.toml" --out "$H/runsD/$arm" --set campaign.allow_oversubscription=true > "$H/$arm.run.log" 2>&1 &
  PIDS="$PIDS $!"
done
sleep 90
cd "$H"
nice -n 5 python3 sampler.py runsD samplesD/samples.jsonl 30 89 &
SP=$!
log "sampler pid $SP; runs $PIDS"
wait $PIDS
sleep 60
kill $SP 2>/dev/null
log "hunt D done"
touch "$H/D_DONE"
