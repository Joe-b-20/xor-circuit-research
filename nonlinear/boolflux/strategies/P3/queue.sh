#!/bin/bash
# Run job.sh lines sequentially (one CPU): queue.sh SPECFILE ; each line: START MODE CAPGD SEED SECS TAG [extra]
S=/home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P3
while read -r line; do
  [ -z "$line" ] && continue
  case "$line" in \#*) continue;; esac
  echo "$(date -u +%T) start $line"
  $S/job.sh $line
  set -- $line
  echo "$(date -u +%T) end $6: $(head -1 /home/joebachir20/xs-campaigns/2026-11-15-targets/P3/runs/$6/record.txt 2>/dev/null | cut -c1-160) | $(tail -1 /home/joebachir20/xs-campaigns/2026-11-15-targets/P3/runs/$6/record.txt 2>/dev/null | cut -c1-120)"
done < "$1"
