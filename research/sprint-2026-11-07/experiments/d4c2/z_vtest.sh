#!/bin/bash
# z_vtest.sh -- exercise e5_verify.py on d4c's 89-gate smoke witness (restricted L2 pool run), then remove the
# test output from found/ so that found/ only ever holds <= 88 circuits.
cd ~/xs-campaigns/2026-11-07-sprint/d4c2 || exit 1
export PYTHONDONTWRITEBYTECODE=1
cp ../d4c/c3_smokeL89.json /tmp/d4c2_vtest.json
python3 e5_verify.py /tmp/d4c2_vtest.json 2>&1 | tee z_vtest.out
ls -la found
rm -f found/aes-mixcolumns-xor89-depth4.circ.txt found/aes-mixcolumns.mat.txt /tmp/d4c2_vtest.json
ls -la found
