#!/bin/bash
# Generate REPORT.md, confirm encoding/size, confirm the git repository is untouched.
cd ~/xs-campaigns/2026-11-07-sprint/lb76 || exit 1
python3 make_report.py
file REPORT.md
head -3 REPORT.md
echo "lines: $(grep -c "" REPORT.md)"
ls -la REPORT.md
cd ~/xor-circuit-research || exit 1
echo "git status (empty means clean):"
git status --short | head -5
