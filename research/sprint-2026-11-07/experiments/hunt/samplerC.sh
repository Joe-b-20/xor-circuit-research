#!/bin/bash
# Sampler for hunt arm C: waits for runs/C to exist, then samples all arms (A and B are stopped
# by then, so only C changes) into samplesC/samples.jsonl until C_DONE appears.
set -u
H="$HOME/xs-campaigns/2026-11-07-sprint/hunt"
mkdir -p "$H/samplesC"
while [ ! -d "$H/runs/C/workers" ]; do sleep 30; done
cd "$H"
nice -n 5 python3 sampler.py runs samplesC/samples.jsonl 30 89 &
SP=$!
while [ ! -f "$H/C_DONE" ]; do sleep 60; done
sleep 60
kill $SP 2>/dev/null
