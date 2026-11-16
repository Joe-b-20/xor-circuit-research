#!/bin/bash
# aes-sbox-a28-ad5-g125-gd24-T03-night-T03-1: the command recorded in the campaign sidecar (~/xs-campaigns/2026-11-16-night/T03/found/conjpull-a28-ad5-g125-gd24-f244b8aa4f.circ.txt, 2026-11-16T04:09:43Z).
# Repository paths are written "$REPO"; other paths ("$HOME"/...) are files of the campaign machine.
# The start circuit is logs/aes-sbox-a28-ad5-g125-gd24-T03-night-T03-1/start.circ.txt here.
# A time-budgeted search: a re-run gives a verified circuit, not necessarily this one.
# As recorded:
#   /usr/bin/python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/campaigns/targets/ops/conjpull.py --in /home/joebachir20/xs-campaigns/2026-11-16-night/starts/aes-sbox-a28-ad5-g126-gd23-0c61a5821a27-a28-ad5-g126-gd23.circ.txt --target T03 --seed 21890 --seconds 960 --out /home/joebachir20/xs-campaigns/2026-11-16-night/T03/runs/T03/conjpull-166 --conj id --schedule g:24:300,m:22:600 --repair-keep alt
REPO=${REPO:-$(git rev-parse --show-toplevel)}
/usr/bin/python3 "$REPO"/nonlinear/boolflux/campaigns/targets/ops/conjpull.py --in "$REPO"/nonlinear/boolflux/results/targets/T03/logs/aes-sbox-a28-ad5-g125-gd24-T03-night-T03-1/start.circ.txt --target T03 --seed 21890 --seconds 960 --out "$HOME"/xs-campaigns/2026-11-16-night/T03/runs/T03/conjpull-166 --conj id --schedule g:24:300,m:22:600 --repair-keep alt
