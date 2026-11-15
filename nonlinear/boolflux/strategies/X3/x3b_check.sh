#!/bin/bash
# X3b: syntax check of X3's files after X3 stopped mid-edit (2026-11-15 ~03:05 UTC)
cd ~/xcr-boolflux/nonlinear/boolflux/strategies/X3 || exit 1
ls -lt --time-style=+%m-%d_%H:%M:%S | head -8
for f in *.py; do python3 -W error -m py_compile "$f" 2>&1 | tail -1 | sed "s/^/$f: /"; done
mkdir -p /tmp/x3b_bin
for f in *.c; do gcc -O2 -o "/tmp/x3b_bin/${f%.c}" "$f" -lm 2>&1 | grep -iE "error|warning: missing" | sed "s/^/$f: /"; echo "compiled $f rc=${PIPESTATUS[0]}"; done
for f in *.sh; do bash -n "$f" || echo "BAD SH $f"; done
echo "CR bytes:"; grep -lU $'\r' * 2>/dev/null
echo "md table rows not closed:"; for f in *.md; do awk -v F="$f" '/^\|/ && !/\|[[:space:]]*$/ {print F": "NR": "$0}' "$f"; done
echo "md: odd number of backticks per line:"; for f in *.md; do awk -v F="$f" '{n=gsub(/`/,"`"); if(n%2) print F": "NR": "$0}' "$f"; done
echo "done"
