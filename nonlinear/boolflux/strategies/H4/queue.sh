#!/bin/bash
# queue.sh QUEUEFILE LOG : run the lines of QUEUEFILE one after another (appendable while
# running); each line is "TIMEOUT_SECONDS command ...".  A line "END" stops the runner.
q=$1; log=$2; i=1
cd "$(dirname "$0")"
while true; do
  line=$(sed -n "${i}p" "$q")
  if [ -z "$line" ]; then sleep 5; continue; fi
  [ "$line" = "END" ] && break
  t=${line%% *}; cmd=${line#* }
  echo "### $(date -u +%H:%M:%S) start [$i] $cmd" >> "$log"
  timeout "$t" bash -c "$cmd" >> "$log" 2>&1
  echo "### $(date -u +%H:%M:%S) end [$i] rc=$?" >> "$log"
  i=$((i+1))
done
