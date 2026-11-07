#!/bin/bash
# qcert: the complete verification of the delivered files, one python process at a time.
# Regeneration (gen_certs.py, needs numpy + scipy, ~2 min) is NOT part of this script; everything below is a check.
#   check_ext75.py  : independent exact checker of every certificate and of the coverage of the 195 claims (stdlib only, ~1 s)
#   crosscheck.py   : the generator's and the checker's system definitions are identical; key/claim sets match qbound/qcheck (~3 s)
#   stress_ext.py   : new rows on 13 controls + 303 real circuits, 4 orbit steps each (~15 s)
#   mutate_test.py  : mutation tests of the checker (~8 min)
set -e
cd "$(dirname "$0")"
nice -n 8 python3 check_ext75.py CERTIFICATES_EXT75.json
nice -n 8 python3 crosscheck.py
nice -n 8 python3 stress_ext.py > stress_ext.log 2>&1 && tail -1 stress_ext.log
nice -n 8 python3 mutate_test.py 1 | tail -1
sha256sum -c SHA256SUMS.txt
echo "QCERT ALL CHECKS PASSED"
