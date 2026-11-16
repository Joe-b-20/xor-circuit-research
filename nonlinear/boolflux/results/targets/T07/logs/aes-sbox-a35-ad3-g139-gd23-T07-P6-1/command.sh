#!/bin/bash
# aes-sbox-a35-ad3-g139-gd23-T07-P6-1: the command recorded in the campaign sidecar (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g139-gd23-703f7ce121a7.circ.txt, 2026-11-15T22:39:36Z).
# Repository paths are written "$REPO"; other paths ("$HOME"/...) are files of the campaign machine.
# The start circuit is logs/aes-sbox-a35-ad3-g139-gd23-T07-P6-1/start.circ.txt here.
# A time-budgeted search: a re-run gives a verified circuit, not necessarily this one.
# As recorded:
#   bash /home/joebachir20/xs-campaigns/2026-11-15-targets/P6/runs/t07c3.sh 140 /home/joebachir20/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g140-gd25-xx105-35.circ.txt 12 (conjugate lam 250 k 4; stage dir /home/joebachir20/xs-campaigns/2026-11-15-targets/P6/runs/c3-140/x-250-4-b)
REPO=${REPO:-$(git rev-parse --show-toplevel)}
bash "$HOME"/xs-campaigns/2026-11-15-targets/P6/runs/t07c3.sh 140 "$HOME"/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g140-gd25-xx105-35.circ.txt 12 (conjugate lam 250 k 4; stage dir "$HOME"/xs-campaigns/2026-11-15-targets/P6/runs/c3-140/x-250-4-b)
