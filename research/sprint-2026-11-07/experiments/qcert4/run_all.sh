#!/bin/bash
# qcert4: the complete check, one python process at a time under nice 8.  check_cases4.py, mutate4.py and stats4.py
# need the standard library only; crosscheck4.py and stress_ext4.py import the package copy / numpy through
# gen_certs4 -> gen_certs3_copy (no LP is solved by any of them).  Regeneration: gen_certs4.py, gen_partial4.py.
set -eo pipefail
cd "$(dirname "$0")"
export PYTHONDONTWRITEBYTECODE=1
t() { date -u +%s; }
T0=$(t); nice -n 8 python3 check_cases4.py CERTIFICATES_CASES75_B4.json > s05_check.out; tail -3 s05_check.out; echo "check_cases4.py: $(( $(t) - T0 )) s"
T0=$(t); nice -n 8 python3 crosscheck4.py > s05_cross.out; tail -1 s05_cross.out;                    echo "crosscheck4.py: $(( $(t) - T0 )) s"
T0=$(t); nice -n 8 python3 mutate4.py 1 > s05_mutate.out; tail -1 s05_mutate.out;                   echo "mutate4.py: $(( $(t) - T0 )) s"
T0=$(t); nice -n 8 python3 stress_ext4.py > s05_stress.out; tail -1 s05_stress.out;                 echo "stress_ext4.py: $(( $(t) - T0 )) s"
T0=$(t); nice -n 8 python3 stats4.py > s05_stats.out; echo "stats4.py: $(( $(t) - T0 )) s"
sha256sum -c SHA256SUMS.txt
echo "QCERT4 ALL CHECKS PASSED"
