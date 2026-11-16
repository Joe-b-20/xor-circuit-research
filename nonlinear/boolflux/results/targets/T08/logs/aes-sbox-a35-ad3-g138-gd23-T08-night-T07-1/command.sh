#!/bin/bash
# aes-sbox-a35-ad3-g138-gd23-T08-night-T07-1: the command recorded in the campaign sidecar (~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g138-gd23-3ed8aa97bd.circ.txt, 2026-11-16T07:05:28Z).
# Repository paths are written "$REPO"; other paths ("$HOME"/...) are files of the campaign machine.
# The start circuit is logs/aes-sbox-a35-ad3-g138-gd23-T08-night-T07-1/start.circ.txt here.
# A time-budgeted search: a re-run gives a verified circuit, not necessarily this one.
# As recorded:
#   /usr/bin/python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/campaigns/targets/ops/conjpull.py --in /home/joebachir20/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g138-gd24-f27addd959.circ.txt --target T07 --seed 706888 --seconds 280 --out /home/joebachir20/xs-campaigns/2026-11-16-night/T07/runs/T07/conjpull-508 --conj id --repair-keep alt --schedule k:27:240
REPO=${REPO:-$(git rev-parse --show-toplevel)}
/usr/bin/python3 "$REPO"/nonlinear/boolflux/campaigns/targets/ops/conjpull.py --in "$REPO"/nonlinear/boolflux/results/targets/T08/logs/aes-sbox-a35-ad3-g138-gd23-T08-night-T07-1/start.circ.txt --target T07 --seed 706888 --seconds 280 --out "$HOME"/xs-campaigns/2026-11-16-night/T07/runs/T07/conjpull-508 --conj id --repair-keep alt --schedule k:27:240
