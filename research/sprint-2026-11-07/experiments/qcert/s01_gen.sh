#!/bin/bash
cd ~/xs-campaigns/2026-11-07-sprint/qcert
nice -n 8 python3 gen_certs.py > s01_gen.out 2>&1
echo "exit $?" >> s01_gen.out
