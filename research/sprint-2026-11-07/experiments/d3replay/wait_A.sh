#!/bin/bash
# Poll replay A until it finishes or MAXWAIT seconds elapse; print progress.
L=/home/joebachir20/xs-campaigns/2026-11-07-sprint/d3replay/logs/A_run.log
F=$(ls /home/joebachir20/xs-campaigns/2026-11-07-sprint/d3replay/A/lb93/verification/run_*/full_verification.log 2>/dev/null | head -1)
MAXWAIT="${1:-540}"
t=0
while ! grep -q "^RC=" "$L" && [ "$t" -lt "$MAXWAIT" ]; do sleep 15; t=$((t+15)); done
echo "waited ${t}s; log lines: $(wc -l < "$F")"
grep -E "^(PASS|FAIL)" "$F" | cut -c1-120 | tail -8
tail -3 "$L"
