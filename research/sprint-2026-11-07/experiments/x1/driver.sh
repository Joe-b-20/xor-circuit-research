#!/bin/bash
# Waits until hunt arm A has run 3 h (started 03:16 UTC -> 06:16 UTC), stops it cleanly, then runs
# X1 in two halves of 8 workers (1 h each) on the freed cores. Arm B keeps running.
set -u
cd "$HOME/xor-circuit-research" || exit 1
X="$HOME/xs-campaigns/2026-11-07-sprint/x1"
H="$HOME/xs-campaigns/2026-11-07-sprint/hunt"
mkdir -p "$X/runs"
log() { echo "$(date -u +%H:%M:%SZ) $*" >> "$X/driver.log"; }
log "waiting for 06:16 UTC"
while [ "$(date -u +%s)" -lt "$(date -u -d '2026-11-07 06:16:00' +%s)" ]; do sleep 30; done
log "stopping hunt arm A"
python3 search/xorflux stop "$H/runs/A" --wait 180 >> "$X/driver.log" 2>&1
sleep 20
log "starting x1a"
python3 search/xorflux run "$X/x1a.toml" --out "$X/runs/x1a" --set campaign.allow_oversubscription=true > "$X/x1a.run.log" 2>&1
log "x1a exit $?; starting x1b"
python3 search/xorflux run "$X/x1b.toml" --out "$X/runs/x1b" --set campaign.allow_oversubscription=true > "$X/x1b.run.log" 2>&1
log "x1b exit $?"
touch "$X/ALL_DONE"
