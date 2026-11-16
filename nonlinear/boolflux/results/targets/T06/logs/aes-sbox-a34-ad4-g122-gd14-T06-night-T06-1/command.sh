#!/bin/bash
# aes-sbox-a34-ad4-g122-gd14-T06-night-T06-1: the command recorded in the campaign sidecar (~/xs-campaigns/2026-11-16-night/T06/found/conjpull-a34-ad4-g122-gd14-621f73cda5.circ.txt, 2026-11-16T12:16:28Z).
# Repository paths are written "$REPO"; other paths ("$HOME"/...) are files of the campaign machine.
# The start circuit is logs/aes-sbox-a34-ad4-g122-gd14-T06-night-T06-1/start.circ.txt here.
# A time-budgeted search: a re-run gives a verified circuit, not necessarily this one.
# As recorded:
#   /usr/bin/python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/campaigns/targets/ops/conjpull.py --in /home/joebachir20/xs-campaigns/2026-11-16-night/T06/found/conjpull-a34-ad4-g123-gd14-f16a32f201.circ.txt --target T06 --seed 756285 --seconds 900 --out /home/joebachir20/xs-campaigns/2026-11-16-night/T06/runs/p2-T06/conjpull-303 --conj id --repair-keep 0 --schedule m:13:600
REPO=${REPO:-$(git rev-parse --show-toplevel)}
/usr/bin/python3 "$REPO"/nonlinear/boolflux/campaigns/targets/ops/conjpull.py --in "$REPO"/nonlinear/boolflux/results/targets/T06/logs/aes-sbox-a34-ad4-g122-gd14-T06-night-T06-1/start.circ.txt --target T06 --seed 756285 --seconds 900 --out "$HOME"/xs-campaigns/2026-11-16-night/T06/runs/p2-T06/conjpull-303 --conj id --repair-keep 0 --schedule m:13:600
