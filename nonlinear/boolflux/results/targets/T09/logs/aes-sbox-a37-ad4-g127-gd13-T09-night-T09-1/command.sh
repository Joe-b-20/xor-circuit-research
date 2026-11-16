#!/bin/bash
# aes-sbox-a37-ad4-g127-gd13-T09-night-T09-1: the command recorded in the campaign sidecar (~/xs-campaigns/2026-11-16-night/T09/found/conjpull-a37-ad4-g127-gd13-00578f7482.circ.txt, 2026-11-16T09:34:32Z).
# Repository paths are written "$REPO"; other paths ("$HOME"/...) are files of the campaign machine.
# A time-budgeted search: a re-run gives a verified circuit, not necessarily this one.
# As recorded:
#   /usr/bin/python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/campaigns/targets/ops/conjpull.py --in /home/joebachir20/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-E-polish-g129-a36-gd13-ad4.circ.txt --target T09 --seed 75437 --seconds 450 --out /home/joebachir20/xs-campaigns/2026-11-16-night/T09/runs/T09/conjpull-813 --conj id --schedule m:12:400:rk0
REPO=${REPO:-$(git rev-parse --show-toplevel)}
/usr/bin/python3 "$REPO"/nonlinear/boolflux/campaigns/targets/ops/conjpull.py --in "$REPO"/nonlinear/boolflux/results/aes/aes-nist-E-polish-g129-a36-gd13-ad4.circ.txt --target T09 --seed 75437 --seconds 450 --out "$HOME"/xs-campaigns/2026-11-16-night/T09/runs/T09/conjpull-813 --conj id --schedule m:12:400:rk0
