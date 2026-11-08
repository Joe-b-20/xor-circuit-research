#!/bin/bash
# wait.sh FILE [max_seconds]: block until FILE exists (or the timeout), then print progress.
T="$HOME/xs-campaigns/2026-11-07-sprint/translog"
f="$1"; max="${2:-570}"; n=0
while [ ! -f "$f" ] && [ "$n" -lt "$max" ]; do sleep 10; n=$((n + 10)); done
date -u +%H:%M:%SZ
tail -3 "$T/run.log"
wc -l "$T/runs/T1/workers/free-00/translog.jsonl" "$T/samples/samples.jsonl" 2>/dev/null
