#!/bin/bash
# seedlist.sh OUT : every verified circuit file we have (pinned NIST forward NCFF, results/aes, all tracks' found/,
# Track E admitted pools) -> one path per line.  (old-2020 .slp files are not NCFF and are not listed.)
N=~/xcr-boolflux/nonlinear
C=~/xs-campaigns/2026-11-13-aes
{
  ls $N/nist/aes-sbox/*.circ.txt $N/nist/sbox/aes-sbox-fwd-*
  ls $N/boolflux/results/aes/*.circ.txt
  find $C/*/found -name "*.circ.txt" 2>/dev/null
  find $C -path "*admitted/*.bfx" 2>/dev/null
} | sort -u > "$1"
wc -l "$1"
