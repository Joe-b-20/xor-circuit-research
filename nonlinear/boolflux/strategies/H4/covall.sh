#!/bin/bash
# covall.sh JSONL MAXL1 : ad3cov.py on every zero-deficit line
cd "$(dirname "$0")"
n=$(wc -l < "$1")
for i in $(seq 0 $((n-1))); do
  if sed -n "$((i+1))p" "$1" | grep -q '"deficit": 0'; then
    echo "== line $i"; python3 ad3cov.py "$1" $i $2
  fi
done
