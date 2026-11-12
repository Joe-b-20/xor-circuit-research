#!/bin/bash
cd "$(dirname "$0")"
ulimit -v 8000000
python3 review_causal.py "${1:-60}" "${2:-1}" 2>&1 | tee review_causal_out.txt
