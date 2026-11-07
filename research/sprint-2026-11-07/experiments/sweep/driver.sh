#!/bin/bash
# Big-map sweep: after pt2 finishes (predtest/ALL_DONE), run sw1 then sw2 (6 workers, 1 h each).
set -u
cd "$HOME/xor-circuit-research" || exit 1
S="$HOME/xs-campaigns/2026-11-07-sprint/sweep"
mkdir -p "$S/runs"
log() { echo "$(date -u +%H:%M:%SZ) $*" >> "$S/driver.log"; }
log "waiting for predtest/ALL_DONE"
while [ ! -f "$HOME/xs-campaigns/2026-11-07-sprint/predtest/ALL_DONE" ]; do sleep 30; done
log "starting sw1"
python3 search/xorflux run "$S/sw1.toml" --out "$S/runs/sw1" --set campaign.allow_oversubscription=true > "$S/sw1.run.log" 2>&1
log "sw1 exit $?; starting sw2"
python3 search/xorflux run "$S/sw2.toml" --out "$S/runs/sw2" --set campaign.allow_oversubscription=true > "$S/sw2.run.log" 2>&1
log "sw2 exit $?"
touch "$S/ALL_DONE"
