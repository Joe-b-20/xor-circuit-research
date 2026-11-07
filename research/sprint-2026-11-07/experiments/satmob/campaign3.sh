#!/bin/bash
# satmob campaign (replaces campaign2.sh): one solver child at a time, nice 8; idempotent.
cd ~/xs-campaigns/2026-11-07-sprint/satmob
while pgrep -f "mob.py run" > /dev/null; do sleep 5; done
python3 mob.py run repo 1,2 120
for c in sampleC:1011 sampleA:2667 sampleA:884; do python3 mob.py run $c 1,2 120; done
python3 mob.py run repo 1,2 600
for c in sampleA:1626 sampleA:1773; do python3 mob.py run $c 1,2 120; done
python3 mob.py run repo 3 120
python3 mob.py run repo all 600
python3 mob.py run repo all 600 span
python3 mob.py run repo 3 600
for c in sampleC:1011 sampleA:2667 sampleA:884 sampleA:1626 sampleA:1773; do python3 mob.py run $c 1,2 600; done
echo CAMPAIGN3_DONE
