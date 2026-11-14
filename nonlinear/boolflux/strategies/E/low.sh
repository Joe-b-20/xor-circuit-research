#!/bin/bash
# low.sh NAME HOURS POLISH : focused low-AND run (A <= 31 frontier, depth pulls) on CPUs 11,12,13 (xsrun unit xs-E-NAME)
set -e
E=$(cd "$(dirname "$0")" && pwd)
B=~/xs-campaigns/2026-11-13-aes/E/$1
mkdir -p "$B"
{ ls ~/xcr-boolflux/nonlinear/nist/aes-sbox/*.circ.txt; ls ~/xcr-boolflux/nonlinear/nist/sbox/aes-sbox-fwd-*;
  ls ~/xcr-boolflux/nonlinear/boolflux/results/aes/*.circ.txt;
  ls ~/xs-campaigns/2026-11-13-aes/F/found/*.circ.txt ~/xs-campaigns/2026-11-13-aes/D/found/*.circ.txt ~/xs-campaigns/2026-11-13-aes/E/found/*.circ.txt 2>/dev/null;
  ls ~/xs-campaigns/2026-11-13-aes/E/long1/splice/admitted/*.bfx 2>/dev/null; } > "$B/files.list"
cd "$E"
XS_MEM=3G ~/xs-campaigns/guard/xsrun E 11-13 "$1" "$B/run.log" -- python3 "$E/memetic.py" --arm splice --out "$B/run" --hours "$2" \
   --cpus 11,12,13 --polish "$3" --amax 31 --gd-pull 0.5 "$B/files.list"
echo launched "$B" "$(wc -l < $B/files.list) files"
