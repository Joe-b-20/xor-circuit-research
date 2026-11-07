#!/bin/bash
# r1.sh -- run the two fast exact computations back-to-back (one python process at a time).
cd ~/xs-campaigns/2026-11-07-sprint/d4bound || exit 1
sed -i 's/\r$//' d3_subset.py d4_post.py
nice -n 8 timeout 600 python3 d4_post.py 2>&1 | tee d4_post.out
P=$(python3 -c "import json;print(json.dumps(json.load(open('d1_facts.json'))['P89']))")
nice -n 8 timeout 600 python3 d3_subset.py 300 "$P" P89 L0 2>&1 | tee d3_P89-L0pool.out
