#!/bin/bash
# aes-sbox-a32-ad7-g104-gd26-T05-night-T05-1: the command recorded in the campaign sidecar (~/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad7-g104-gd26-8da775ecfd.circ.txt, 2026-11-16T02:10:15Z).
# Repository paths are written "$REPO"; other paths ("$HOME"/...) are files of the campaign machine.
# The start circuit is logs/aes-sbox-a32-ad7-g104-gd26-T05-night-T05-1/start.circ.txt here.
# A time-budgeted search: a re-run gives a verified circuit, not necessarily this one.
# As recorded:
#   /usr/bin/python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/campaigns/targets/ops/conjpull.py --in /home/joebachir20/xs-campaigns/2026-11-15-targets/P4/found/p4-deep236-a32-ad7-g104-gd27.circ.txt --target T05 --seed 423171 --seconds 1000 --out /home/joebachir20/xs-campaigns/2026-11-16-night/T05/runs/T05/conjpull-17 --schedule g:34:300,t:32:300,m:32:360 --repair-keep alt --conj rank:1
REPO=${REPO:-$(git rev-parse --show-toplevel)}
/usr/bin/python3 "$REPO"/nonlinear/boolflux/campaigns/targets/ops/conjpull.py --in "$REPO"/nonlinear/boolflux/results/targets/T05/logs/aes-sbox-a32-ad7-g104-gd26-T05-night-T05-1/start.circ.txt --target T05 --seed 423171 --seconds 1000 --out "$HOME"/xs-campaigns/2026-11-16-night/T05/runs/T05/conjpull-17 --schedule g:34:300,t:32:300,m:32:360 --repair-keep alt --conj rank:1
