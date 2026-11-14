#!/bin/bash
# run_splice.sh NAME : full splice2 enumeration over published + team circuits, 4 shards on CPUs 7-10 (xsrun)
set -e
E=$(cd "$(dirname "$0")" && pwd)
B=~/xs-campaigns/2026-11-13-aes/E/$1
mkdir -p "$B"
{ ls ~/xcr-boolflux/nonlinear/nist/aes-sbox/*.circ.txt; ls ~/xcr-boolflux/nonlinear/nist/sbox/aes-sbox-fwd-*;
  ls ~/xcr-boolflux/nonlinear/boolflux/results/aes/*.circ.txt; ls ~/xs-campaigns/2026-11-13-aes/F/found/*.circ.txt; } > "$B/files.list"
cd "$E"
i=0
for cpu in 7 8 9 10; do
  XS_MEM=1G ~/xs-campaigns/guard/xsrun E $cpu "splice-$1-$i" "$B/shard$i.log" -- python3 "$E/splice2.py" "$B/shard$i" --shard $i/4 "$B/files.list"
  i=$((i+1))
done
echo launched
