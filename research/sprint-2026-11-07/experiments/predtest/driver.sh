#!/bin/bash
# After X1 finishes (x1/ALL_DONE, ~08:25 UTC): stop hunt arm B, launch the PES run on the kste
# plateaus (kste1, 8 cores, 16 h) and the prediction tests pt1 (6 workers, 2 h) then pt2 (8
# workers, 2 h).
set -u
cd "$HOME/xor-circuit-research" || exit 1
S="$HOME/xs-campaigns/2026-11-07-sprint"
P="$S/predtest"
mkdir -p "$P/runs"
log() { echo "$(date -u +%H:%M:%SZ) $*" >> "$P/driver.log"; }
log "waiting for x1/ALL_DONE"
while [ ! -f "$S/x1/ALL_DONE" ]; do sleep 30; done
log "stopping hunt arm B"
python3 search/xorflux stop "$S/hunt/runs/B" --wait 180 >> "$P/driver.log" 2>&1
sleep 15
log "launching kste1 (PES on kste plateaus, 8 cores, 16 h)"
( cd "$S/pes-kste" && mkdir -p runs && export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 && \
  timeout -s TERM 59400 python3 pes/pes2_run.py runs/kste1 --hours 16 --targets mc --cores mc=8 \
    --seeds-json "$S/pes-kste/kste_seeds.json" --window-own --exclude-giants --giant-choices 1000 \
    --descent bfs >> runs/kste1.out 2>&1 < /dev/null ) &
KPID=$!
log "kste1 driver pid $KPID"
sleep 30
log "starting pt1"
python3 search/xorflux run "$P/pt1.toml" --out "$P/runs/pt1" --set campaign.allow_oversubscription=true > "$P/pt1.run.log" 2>&1
log "pt1 exit $?; starting pt2"
python3 search/xorflux run "$P/pt2.toml" --out "$P/runs/pt2" --set campaign.allow_oversubscription=true > "$P/pt2.run.log" 2>&1
log "pt2 exit $?"
touch "$P/ALL_DONE"
wait
