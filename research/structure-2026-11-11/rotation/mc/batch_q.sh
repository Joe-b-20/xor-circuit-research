#!/bin/bash
# More heuristic seeds for Q_4 and Q_5 (question: anything below 10m with block cancellation?). 3 cores, 360 s each.
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE/.."
mkdir -p mc/logs
(bash run_quick.sh 4 360 s2 2 > mc/logs/quick_q4_s2.log 2>&1) &
(bash run_quick.sh 4 360 s3 3 > mc/logs/quick_q4_s3.log 2>&1) &
(bash run_quick.sh 5 360 s1 1 > mc/logs/quick_q5_s1.log 2>&1) &
wait
grep -h stopped mc/logs/quick_q4_s2.log mc/logs/quick_q4_s3.log mc/logs/quick_q5_s1.log
