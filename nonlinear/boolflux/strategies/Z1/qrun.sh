#!/bin/bash
# qrun.sh QUEUEFILE [WAITUNIT...]
#   Sequential job queue for one CPU: waits until every WAITUNIT (systemd user unit) is inactive,
#   then runs the lines of QUEUEFILE one by one (bash -c), remembering progress in QUEUEFILE.done.
#   New lines may be appended at any time; idles (polls every 30 s) when the queue is empty;
#   exits when QUEUEFILE.stop exists.  Logs to stdout (the xsrun log).
Q=$1; shift
for u in "$@"; do while systemctl --user is-active -q $u; do sleep 20; done; done
touch $Q.done
while [ ! -f $Q.stop ]; do
  n=$(wc -l < $Q.done)
  line=$(sed -n "$((n + 1))p" $Q)
  if [ -z "$line" ]; then
    if [ "$(wc -l < $Q)" -gt "$n" ]; then echo "$line" >> $Q.done; continue; fi
    sleep 30; continue
  fi
  echo "$(date -u +%FT%T) START $line"
  bash -c "$line"
  echo "$(date -u +%FT%T) END rc=$? $line"
  echo "$line" >> $Q.done
done
echo "$(date -u +%FT%T) stop file seen, exiting"
