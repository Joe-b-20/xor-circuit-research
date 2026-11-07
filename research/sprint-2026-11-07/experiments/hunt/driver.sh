#!/bin/bash
# Runs hunt arms A and B (6 workers each) from the repo's v8 code, both at once, in the foreground
# of this script so that the wsl.exe that started it keeps the WSL instance alive.
set -u
cd "$HOME/xor-circuit-research" || exit 1
H="$HOME/xs-campaigns/2026-11-07-sprint/hunt"
mkdir -p "$H/runs"
date -u +"%Y-%m-%dT%H:%M:%SZ start" >> "$H/driver.log"
python3 search/xorflux run "$H/A.toml" --out "$H/runs/A" --set campaign.allow_oversubscription=true > "$H/A.run.log" 2>&1 &
PA=$!
sleep 5
python3 search/xorflux run "$H/B.toml" --out "$H/runs/B" --set campaign.allow_oversubscription=true > "$H/B.run.log" 2>&1 &
PB=$!
echo "A pid $PA, B pid $PB" >> "$H/driver.log"
wait $PA; echo "A exit $? $(date -u +%H:%M:%SZ)" >> "$H/driver.log"
wait $PB; echo "B exit $? $(date -u +%H:%M:%SZ)" >> "$H/driver.log"
touch "$H/ALL_DONE"
