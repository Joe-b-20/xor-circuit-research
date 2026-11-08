#!/bin/bash
# exp2 driver (detached): 2 h / 8-worker campaign under nice -n 8; DONE marker at the end.
set -u
T="$HOME/xs-campaigns/2026-11-07-sprint/translog"
E="$T/exp2"
cd "$T" || exit 1
log() { echo "$(date -u +%H:%M:%SZ) $*" >> "$E/driver.log"; }
mkdir -p "$E/runs"
log "load: $(cut -d' ' -f1-3 /proc/loadavg)"
log "starting E2"
nice -n 8 python3 "$T/xorflux-translog/xorflux" run "$E/E2.toml" --out "$E/runs/E2" \
    --set campaign.allow_oversubscription=true > "$E/E2.run.log" 2>&1
log "run exited $?; load: $(cut -d' ' -f1-3 /proc/loadavg)"
touch "$E/DONE"
log "DONE"
