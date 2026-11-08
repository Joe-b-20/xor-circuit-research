#!/bin/bash
# The 20-minute test: T0 (log off) and T1 (log on) concurrently, one worker each, nice -n 8,
# plus the hunt's 30 s sampler over both run directories (what the sampler sees vs the log).
# Usage: run.sh            (writes runs/T0, runs/T1, samples/samples.jsonl, run.log, DONE)
set -u
T="$HOME/xs-campaigns/2026-11-07-sprint/translog"
cd "$T" || exit 1
log() { echo "$(date -u +%H:%M:%SZ) $*" >> "$T/run.log"; }
rm -rf "$T/runs" "$T/samples" "$T/DONE"
mkdir -p "$T/runs" "$T/samples"
log "load: $(cut -d' ' -f1-3 /proc/loadavg)"
PIDS=""
for arm in T0 T1; do
  log "starting $arm"
  nice -n 8 python3 "$T/xorflux-translog/xorflux" run "$T/$arm.toml" --out "$T/runs/$arm" \
      --set campaign.allow_oversubscription=true > "$T/$arm.run.log" 2>&1 &
  PIDS="$PIDS $!"
done
sleep 30
nice -n 5 python3 "$HOME/xs-campaigns/2026-11-07-sprint/hunt/sampler.py" "$T/runs" "$T/samples/samples.jsonl" 30 89 &
SP=$!
log "sampler pid $SP; runs $PIDS"
wait $PIDS
log "runs done; load: $(cut -d' ' -f1-3 /proc/loadavg)"
sleep 5
touch "$T/samples/ALL_DONE"
sleep 35
kill $SP 2>/dev/null
touch "$T/DONE"
log "DONE"
