#!/bin/bash
# z_int.sh TAG -- send SIGINT to the python solver process of run TAG (CP-SAT stops and the json is written)
for p in $(pgrep -f "python3 e3_run.py $1 "); do
  if [ "$(cat /proc/$p/comm)" = "python3" ]; then kill -INT $p; echo "SIGINT $p"; fi
done
