#!/bin/bash
# usage: lsdocs.sh folder...  (lists md/txt/json docs, relative to archive research/)
cd ~/xs-campaigns/2026-11-07-sprint/import/zip/research/ || exit 1
for d in "$@"; do
  echo "=== $d"
  find "$d" -type f \( -name "*.md" -o -name "*.txt" -o -name "*.json" \) -size -400k | grep -v -i "sha256\|manifest" | head -25
done
