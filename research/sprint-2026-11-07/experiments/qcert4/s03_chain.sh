#!/bin/bash
cd ~/xs-campaigns/2026-11-07-sprint/qcert4
export PYTHONDONTWRITEBYTECODE=1
T0=1794108964; nice -n 8 python3 mutate4.py 1 > s03_mutate.out 2>&1; echo "mutate4.py rc=0 1794108964 s" >> s03_chain.log
T0=1794108964; nice -n 8 python3 stress_ext4.py > s03_stress.out 2>&1; echo "stress_ext4.py rc=0 1794108964 s" >> s03_chain.log
echo CHAIN_DONE >> s03_chain.log
