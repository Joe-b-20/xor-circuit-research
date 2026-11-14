#!/bin/bash
# long.sh NAME HOURS POLISH : splice arm on CPUs 7,8 and control arm on CPUs 9,10, same input pool (xsrun units)
set -e
E=$(cd "$(dirname "$0")" && pwd)
B=~/xs-campaigns/2026-11-13-aes/E/$1
mkdir -p "$B"
{ ls ~/xcr-boolflux/nonlinear/nist/aes-sbox/*.circ.txt; ls ~/xcr-boolflux/nonlinear/nist/sbox/aes-sbox-fwd-*;
  ls ~/xcr-boolflux/nonlinear/boolflux/results/aes/*.circ.txt; ls ~/xs-campaigns/2026-11-13-aes/F/found/*.circ.txt; } > "$B/files.list"
cd "$E"
XS_MEM=2G ~/xs-campaigns/guard/xsrun E 7,8 "$1-splice" "$B/splice.log" -- python3 "$E/memetic.py" --arm splice --out "$B/splice" --hours "$2" --cpus 7,8 --polish "$3" "$B/files.list"
XS_MEM=2G ~/xs-campaigns/guard/xsrun E 9,10 "$1-control" "$B/control.log" -- python3 "$E/memetic.py" --arm control --out "$B/control" --hours "$2" --cpus 9,10 --polish "$3" "$B/files.list"
echo launched "$B"
