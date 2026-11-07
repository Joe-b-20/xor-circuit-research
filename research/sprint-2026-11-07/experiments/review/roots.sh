#!/bin/bash
cd ~/xs-campaigns/2026-11-07-sprint/hunt/runs || exit 1
for a in A B C; do
  for w in 0 1 2 3 4 5; do
    printf "%s free-0%s first root: " "$a" "$w"
    grep -m1 '"ev":"improve"' "$a/workers/free-0$w/events.jsonl" | grep -o '"root":"[^"]*"'
  done
done
echo ====
for a in A C; do
  printf "%s free-00 restart roots: " "$a"
  grep -h '"ev":"restart"' "$a/workers/free-00/events.jsonl" | grep -o '"id":"[^"]*"' | head -4 | tr '\n' ' '
  echo
done
