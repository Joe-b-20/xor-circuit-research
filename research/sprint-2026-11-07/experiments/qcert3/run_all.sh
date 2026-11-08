#!/bin/bash
# qcert3: the complete check (standard library suffices for check_cases3.py, fm_tab3.py and mutate3.py; crosscheck3.py
# and stress_ext3.py import the package copy / numpy through gen_certs3 / stress_pkg).  One python process at a time.
set -eo pipefail
cd "$(dirname "$0")"
t() { date -u +%s; }
T0=$(t); nice -n 8 python3 check_cases3.py CERTIFICATES_CASES75_B3.json | tail -2;        echo "check_cases3.py: $(( $(t) - T0 )) s"
T0=$(t); nice -n 8 python3 fm_tab3.py | tail -1;                                         echo "fm_tab3.py: $(( $(t) - T0 )) s"
T0=$(t); nice -n 8 python3 crosscheck3.py | tail -1;                                     echo "crosscheck3.py: $(( $(t) - T0 )) s"
T0=$(t); nice -n 8 python3 mutate3.py 1 | tail -1;                                       echo "mutate3.py: $(( $(t) - T0 )) s"
T0=$(t); nice -n 8 python3 stress_ext3.py | tail -1;                                     echo "stress_ext3.py: $(( $(t) - T0 )) s"
sha256sum -c SHA256SUMS.txt
echo "QCERT3 ALL CHECKS PASSED"
