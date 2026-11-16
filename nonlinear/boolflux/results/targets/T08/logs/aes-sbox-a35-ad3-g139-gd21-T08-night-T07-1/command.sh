#!/bin/bash
# aes-sbox-a35-ad3-g139-gd21-T08-night-T07-1: the command recorded in the campaign sidecar (~/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g139-gd21-f71f0d11d1.circ.txt, 2026-11-16T12:09:47Z).
# Repository paths are written "$REPO"; other paths ("$HOME"/...) are files of the campaign machine.
# The start circuit is logs/aes-sbox-a35-ad3-g139-gd21-T08-night-T07-1/start.circ.txt here.
# A time-budgeted search: a re-run gives a verified circuit, not necessarily this one.
# As recorded:
#   /usr/bin/python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/campaigns/targets/ops/conjpull.py --in /home/joebachir20/xs-campaigns/2026-11-16-night/T07/found/conjpull-a35-ad3-g139-gd22-f26965830b.circ.txt --target T07 --seed 321738 --seconds 280 --out /home/joebachir20/xs-campaigns/2026-11-16-night/T07/runs/p2-T07/conjpull-277 --conj id --repair-keep alt --schedule k:23:240
REPO=${REPO:-$(git rev-parse --show-toplevel)}
/usr/bin/python3 "$REPO"/nonlinear/boolflux/campaigns/targets/ops/conjpull.py --in "$REPO"/nonlinear/boolflux/results/targets/T08/logs/aes-sbox-a35-ad3-g139-gd21-T08-night-T07-1/start.circ.txt --target T07 --seed 321738 --seconds 280 --out "$HOME"/xs-campaigns/2026-11-16-night/T07/runs/p2-T07/conjpull-277 --conj id --repair-keep alt --schedule k:23:240
