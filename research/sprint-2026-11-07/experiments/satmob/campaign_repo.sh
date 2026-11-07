#!/bin/bash
# one solver child at a time, nice 8; idempotent (results.jsonl is consulted before every instance)
cd ~/xs-campaigns/2026-11-07-sprint/satmob
python3 mob.py run repo 1,2 120
python3 mob.py run repo 3 120
python3 mob.py run repo 1,2 600
python3 mob.py run repo 3 600
echo REPO_CAMPAIGN_DONE
