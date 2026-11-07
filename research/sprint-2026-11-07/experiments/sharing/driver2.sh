#!/bin/bash
cd ~/xs-campaigns/2026-11-07-sprint/sharing || exit 1
until grep -q "driver end" driver.log; do sleep 10; done
nice -n 8 python3 -u cone_core.py > cone_core.log 2>&1
echo "cone_core(25) done 2026-11-07T22:37:42Z" >> driver.log
