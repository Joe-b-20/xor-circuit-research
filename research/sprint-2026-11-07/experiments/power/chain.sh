#!/bin/bash
# wait for part 1, add the P2 anchors, then run the solver within the budget (minutes, arg 1)
cd "$(dirname "$0")"
while [ ! -s anchors.json ] || [ ! -s windows.json ] || pgrep -f "python3 anchors.py" > /dev/null; do sleep 10; done
nice -n 8 python3 anchors_p2.py > anchors_p2.out 2>&1
nice -n 8 python3 run_power.py "${1:-85}" "${2:-12}" > run_power.out 2>&1
touch POWER_DONE
