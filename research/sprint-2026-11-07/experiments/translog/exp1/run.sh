#!/bin/bash
# exp1 driver (detached): the 1 h / 12-worker campaign under nice -n 8 plus the hunt's 30 s
# sampler over its run directory; DONE marker at the end.  Log: exp1/driver.log.
set -u
T="$HOME/xs-campaigns/2026-11-07-sprint/translog"
E="$T/exp1"
cd "$T" || exit 1
log() { echo "$(date -u +%H:%M:%SZ) $*" >> "$E/driver.log"; }
mkdir -p "$E/runs" "$E/samples"
log "load: $(cut -d' ' -f1-3 /proc/loadavg)"
log "starting E1"
nice -n 8 python3 "$T/xorflux-translog/xorflux" run "$E/E1.toml" --out "$E/runs/E1" \
    --set campaign.allow_oversubscription=true > "$E/E1.run.log" 2>&1 &
RP=$!
sleep 45
nice -n 5 python3 "$HOME/xs-campaigns/2026-11-07-sprint/hunt/sampler.py" "$E/runs" "$E/samples/samples.jsonl" 30 89 &
SP=$!
log "run pid $RP sampler pid $SP"
wait $RP
log "run exited $?; load: $(cut -d' ' -f1-3 /proc/loadavg)"
sleep 5
touch "$E/samples/ALL_DONE"
sleep 35
kill $SP 2>/dev/null
touch "$E/DONE"
log "DONE"
