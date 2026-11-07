#!/bin/bash
# qcheck: re-run the qbound LP scans with the UNCHANGED qb_lp.py (base, Gstar, N1, GstarN1); one python at a time
cd ~/xs-campaigns/2026-11-07-sprint/qbound
for v in base Gstar N1 GstarN1; do
  echo "== $v  $(date -u +%H:%M:%S)"
  nice -n 12 python3 qb_lp.py scan $v 75 2>&1 | grep -v "^G=75"
done
echo "== done $(date -u +%H:%M:%S)"
