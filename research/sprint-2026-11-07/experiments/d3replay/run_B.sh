#!/bin/bash
# Replay package B (restored Ordinary Union checkpoint).
#   ./run_B.sh            default mode, timeout 1800 s
#   ./run_B.sh fullcore   --full-core, timeout 1800 s
R=/home/joebachir20/xs-campaigns/2026-11-07-sprint/d3replay/B/restored
cd "$R" || exit 9
MODE="${1:-default}"
if [ "$MODE" = "fullcore" ]; then FLAG="--full-core"; else FLAG=""; fi
echo "START $(date -u +%Y-%m-%dT%H:%M:%SZ) MODE=$MODE"
echo "CWD $(pwd)"
echo "CMD: nice -n 8 timeout 1800 python3 ordinary_completion/verify_checkpoint.py $FLAG"
echo "LOAD_BEFORE: $(cat /proc/loadavg)"
SECONDS=0
nice -n 8 timeout 1800 python3 ordinary_completion/verify_checkpoint.py $FLAG
RC=$?
echo "RC=$RC WALL=${SECONDS}s END $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "LOAD_AFTER: $(cat /proc/loadavg)"
