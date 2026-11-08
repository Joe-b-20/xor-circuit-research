#!/bin/bash
# qcert2: the complete verification of the delivered files, one python process at a time.
# Regeneration (gen_certs2.py, needs numpy + scipy, ~2 min) is NOT part of this script; everything below is a check.
#   check_cases75.py : independent exact checker of every per-case certificate and of the case-enumerating coverage
#                      of the 300 killed keys and the 317 claims (stdlib only, ~3 s; pinned expected counts)
#   crosscheck2.py   : the generator's and the checker's system definitions are identical on every (key, case) node;
#                      key / claim sets match qbound, qreal, qrealcheck and qcert (~30 s)
#   mutate_cases.py  : mutation tests of the checker on every certificate and every claim (~25 s)
#   stress_ext2.py   : batch-1, HUB and DARK rows with strong forms and O1 on 13 controls + 303 real circuits (~40 s)
#   synthetic_hub.py : synthetic local configurations with A >= 1 for the HUB row (~12 s)
set -e
cd "$(dirname "$0")"
nice -n 8 python3 check_cases75.py CERTIFICATES_CASES75.json | tail -2
nice -n 8 python3 crosscheck2.py | tail -3
nice -n 8 python3 mutate_cases.py 1 | tail -1
nice -n 8 python3 stress_ext2.py > stress_ext2.log 2>&1 && tail -1 stress_ext2.log
nice -n 8 python3 synthetic_hub.py > synthetic_hub.log 2>&1 && tail -1 synthetic_hub.log
sha256sum -c SHA256SUMS.txt
echo "QCERT2 ALL CHECKS PASSED"
