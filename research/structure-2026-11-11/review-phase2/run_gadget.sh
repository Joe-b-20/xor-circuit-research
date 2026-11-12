#!/bin/bash
cd "$(dirname "$0")"
ulimit -v 8000000
python3 gadget.py 2>&1 | tee gadget_out.txt
