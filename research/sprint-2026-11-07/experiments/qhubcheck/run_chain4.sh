#!/bin/bash
# qhubcheck chain 4 (after chain 3): diagnose the disputed key
cd ~/xs-campaigns/2026-11-07-sprint/qhubcheck
until [ -f chain3.done ]; do sleep 10; done
echo "== vert_key $(date -u)" > vert_key.log
nice -n 10 timeout 600 python3 vert_key.py 9 6 8 7 0 Mt >> vert_key.log 2>&1
echo "EXIT $? $(date -u)" >> vert_key.log
touch chain4.done
