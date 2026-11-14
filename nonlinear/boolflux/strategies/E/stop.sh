#!/bin/bash
# stop.sh PATTERN : kill Track-E processes whose command line contains PATTERN (default: all of strategies/E)
P=${1:-strategies/E/}
for pid in $(pgrep -f "$P"); do
  [ "$pid" = "$$" ] && continue
  [ "$pid" = "$PPID" ] && continue
  cmd=$(tr '\0' ' ' < /proc/$pid/cmdline 2>/dev/null)
  case "$cmd" in *stop.sh*) continue;; esac
  kill "$pid" 2>/dev/null && echo "killed $pid $cmd"
done
