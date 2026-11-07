#!/bin/bash
# Start hunt arm C (6 workers, 3 h) two minutes after X1 finishes (when arm B is stopped and
# kste1 + pt1 have started), and keep the sampler alive for it.
set -u
cd "$HOME/xor-circuit-research" || exit 1
H="$HOME/xs-campaigns/2026-11-07-sprint/hunt"
log() { echo "$(date -u +%H:%M:%SZ) $*" >> "$H/driverC.log"; }
log "waiting for x1/ALL_DONE"
while [ ! -f "$HOME/xs-campaigns/2026-11-07-sprint/x1/ALL_DONE" ]; do sleep 30; done
sleep 150
log "starting arm C"
python3 search/xorflux run "$H/C.toml" --out "$H/runs/C" --set campaign.allow_oversubscription=true > "$H/C.run.log" 2>&1
log "C exit $?"
touch "$H/C_DONE"
