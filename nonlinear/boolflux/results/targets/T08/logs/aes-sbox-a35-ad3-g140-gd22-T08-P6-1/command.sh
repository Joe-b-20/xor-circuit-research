#!/bin/bash
# aes-sbox-a35-ad3-g140-gd22-T08-P6-1: the command recorded in the campaign sidecar (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g140-gd22-ecd3572a7c9b.circ.txt, 2026-11-15T22:09:30Z).
# Repository paths are written "$REPO"; other paths ("$HOME"/...) are files of the campaign machine.
# The start circuit is logs/aes-sbox-a35-ad3-g140-gd22-T08-P6-1/start.circ.txt here.
# A time-budgeted search: a re-run gives a verified circuit, not necessarily this one.
# As recorded:
#   bash /home/joebachir20/xs-campaigns/2026-11-15-targets/P6/runs/t07c3.sh 140 /home/joebachir20/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g140-gd25-xx105-35.circ.txt 12 (conjugate lam 99 k 0; stage dir /home/joebachir20/xs-campaigns/2026-11-15-targets/P6/runs/c3-140/x-99-0-b)
REPO=${REPO:-$(git rev-parse --show-toplevel)}
bash "$HOME"/xs-campaigns/2026-11-15-targets/P6/runs/t07c3.sh 140 "$HOME"/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g140-gd25-xx105-35.circ.txt 12 (conjugate lam 99 k 0; stage dir "$HOME"/xs-campaigns/2026-11-15-targets/P6/runs/c3-140/x-99-0-b)
