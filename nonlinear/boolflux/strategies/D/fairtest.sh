#!/bin/bash
# Final fair test (2026-11-14): breathe vs kernel-alone control, run as a sequential queue on one CPU.
#   fairtest.sh JOB [JOB ...]   JOB = B127 C127 B133 C133 B124 C124 B116 C116
cd "$(dirname "$0")"
N=$HOME/xcr-boolflux/nonlinear/nist/aes-sbox
RA=$HOME/xcr-boolflux/nonlinear/boolflux/results/aes
O=$HOME/xs-campaigns/2026-11-13-aes/D/fair
mkdir -p $O
for job in "$@"; do
  case ${job:1} in
    127) S=$N/aes-sbox-a33-ad4-g127-gd14-xx94-23.circ.txt; D=14;;
    133) S=$N/aes-sbox-a35-ad4-g133-gd13-xx98-21.circ.txt; D=13;;
    124) S=$RA/aes-nist-bench-rebuild-gd14-g124-a38-gd14-ad4.circ.txt; D=14;;
    116) S=$N/aes-sbox-a33-ad4-g116-gd15-xx83-7.circ.txt; D=15;;
  esac
  echo "$(date -u +%FT%TZ) start $job" >> $O/queue.log
  if [ ${job:0:1} = B ]; then
    python3 breathe.py --start $S --out $O/$job --cap-gd $D --hours 0.27 --t-relax 90 --t-kernel 120 --t-polish 45 --seed 11
  else
    python3 control.py --start $S --out $O/$job --cap-gd $D --seconds 1080 --chunk 270 --seed 11
  fi
  echo "$(date -u +%FT%TZ) end $job" >> $O/queue.log
done
