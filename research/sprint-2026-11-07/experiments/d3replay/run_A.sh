#!/bin/bash
# Replay package A: public depth-3 lower bound 93 (full replay; the wrapper's
# default mode runs verify_complete_92_exclusion.py --full internally).
cd /home/joebachir20/xs-campaigns/2026-11-07-sprint/d3replay/A/lb93 || exit 9
echo "START $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "CWD $(pwd)"
echo "CMD: nice -n 8 timeout 2400 python3 verify_all.py"
echo "LOAD_BEFORE: $(cat /proc/loadavg)"
SECONDS=0
nice -n 8 timeout 2400 python3 verify_all.py
RC=$?
echo "RC=$RC WALL=${SECONDS}s END $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "LOAD_AFTER: $(cat /proc/loadavg)"
