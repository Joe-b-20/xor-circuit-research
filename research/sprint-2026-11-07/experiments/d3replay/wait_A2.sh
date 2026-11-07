#!/bin/bash
# Block until replay A's run log has its RC= line (or MAXWAIT s), then print the run log.
L=/home/joebachir20/xs-campaigns/2026-11-07-sprint/d3replay/logs/A_run.log
MAXWAIT="${1:-1500}"
t=0
until grep -q "^RC=" "$L" || [ "$t" -ge "$MAXWAIT" ]; do sleep 20; t=$((t+20)); done
echo "waited ${t}s at $(date -u +%H:%M:%SZ)"
cat "$L"
