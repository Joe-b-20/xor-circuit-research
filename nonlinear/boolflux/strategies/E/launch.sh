#!/bin/bash
# launch.sh NAME SECONDS SEEDS CASES ARMS [CPUS]  -> batch in ~/xs-campaigns/2026-11-13-aes/E/NAME (background)
set -e
E=$(cd "$(dirname "$0")" && pwd)
B=~/xs-campaigns/2026-11-13-aes/E/$1
mkdir -p "$B"
python3 "$E/make_plan.py" "$B/plan.json" "$2" "$3" "$4" "$5"
CPUS=${6:-5,6,7,8,9}
setsid nohup python3 "$E/batch.py" "$B/plan.json" "$B" --cpus "$CPUS" > "$B/batch.log" 2>&1 < /dev/null &
echo "launched $B pid $!"
