#!/bin/bash
# final: name the report, hash the static deliverables, run the complete check once
cd ~/xs-campaigns/2026-11-07-sprint/qcert
mv -f R4.md REPORT.md
rm -rf __pycache__
sha256sum CERTIFICATES_EXT75.json scan_ext75.json PROOF_ADDENDUM.md REPORT.md gen_certs.py check_ext75.py mutate_test.py stress_ext.py crosscheck.py stress_pkg.py profile_real_copy.py run_all.sh gen_certs.log > SHA256SUMS.txt
cat SHA256SUMS.txt
echo "=== run_all.sh $(date -u +%H:%M:%S)"
bash run_all.sh > run_all.log 2>&1; echo "run_all exit $?" >> run_all.log
tail -12 run_all.log
rm -rf __pycache__
echo "=== done $(date -u +%H:%M:%S)"
ls -la
