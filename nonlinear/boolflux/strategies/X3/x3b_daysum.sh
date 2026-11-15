#!/bin/bash
# X3b: summary of the day-pairs sweep logs
cd ~/xs-campaigns/2026-11-15-study/X3/day-pairs || exit 1
echo "files: $(grep -h '^# ' shard*.log | sort -u | wc -l)"
echo "files without a slack pair: $(grep -h '^# ' shard*.log | sort -u | grep -c ': 0 minimal')"
echo "window runs: $(grep -h '^## ' shard*.log | wc -l)"
echo "COVERABLE/BUILT/TIMEOUT lines: $(cat shard*.log | grep -c 'COVERABLE\|BUILT\|TIMEOUT')"
echo "result histograms:"; grep -h 'dimU, 9-cover' shard*.log | grep -o '{.*}' | sort | uniq -c
echo "x1b files: $(grep -h '^# aes-sbox' shard*.log | sort -u | wc -l)  h2 files: $(grep -h '^# h2-' shard*.log | sort -u | wc -l)"
