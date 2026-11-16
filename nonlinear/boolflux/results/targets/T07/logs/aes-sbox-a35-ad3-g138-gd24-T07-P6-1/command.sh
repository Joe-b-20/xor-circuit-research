#!/bin/bash
# aes-sbox-a35-ad3-g138-gd24-T07-P6-1: the command recorded in the campaign sidecar (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g138-gd24-d6946cbba230.circ.txt, 2026-11-15T22:53:24Z).
# Repository paths are written "$REPO"; other paths ("$HOME"/...) are files of the campaign machine.
# The start circuit is logs/aes-sbox-a35-ad3-g138-gd24-T07-P6-1/start.circ.txt here.
# A time-budgeted search: a re-run gives a verified circuit, not necessarily this one.
# As recorded:
#   cd /home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P6 && python3 kern.py /home/joebachir20/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g139-gd23-703f7ce121a7.circ.txt --caps 35,3,27 --seed 20378 --seconds 240 --out /home/joebachir20/xs-campaigns/2026-11-15-targets/P6/runs/polish139c/c27-sd20378/jobs
REPO=${REPO:-$(git rev-parse --show-toplevel)}
cd "$REPO"/nonlinear/boolflux/strategies/P6 && python3 kern.py "$HOME"/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g139-gd23-703f7ce121a7.circ.txt --caps 35,3,27 --seed 20378 --seconds 240 --out "$HOME"/xs-campaigns/2026-11-15-targets/P6/runs/polish139c/c27-sd20378/jobs
