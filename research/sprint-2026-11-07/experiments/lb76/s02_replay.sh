#!/bin/bash
# Copy the package out of the git repository and replay verify_all.py there under nice.
set -e
LB=~/xs-campaigns/2026-11-07-sprint/lb76
rm -rf "$LB/pkg_copy"
cp -r ~/xor-circuit-research/lower-bound-proofs/mixcolumns-lb75 "$LB/pkg_copy"
cd "$LB/pkg_copy"
echo "start $(date -u +%FT%TZ)"
nice -n 10 python3 verify_all.py > "$LB/replay_verify_all.log" 2>&1
echo "exit $?"
echo "end $(date -u +%FT%TZ)"
tail -n 5 "$LB/replay_verify_all.log"
