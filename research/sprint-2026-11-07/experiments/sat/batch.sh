#!/bin/bash
# Overnight scoped-SAT batch.  One solver child at a time (nice 10, enforced inside
# sat87.solve_instance).  Restartable: skips instances already in results_batch.jsonl.
# Stop cleanly: touch ~/xs-campaigns/2026-11-07-sprint/sat/STOP (checked before every instance).
# Poll for a find: ~/xs-campaigns/2026-11-07-sprint/sat/FOUND_87.
# Plan only (no solver): bash batch.sh --plan
cd ~/xs-campaigns/2026-11-07-sprint/sat || exit 1
exec nice -n 10 python3 batch_driver.py "$@" >> batch.out 2>&1
