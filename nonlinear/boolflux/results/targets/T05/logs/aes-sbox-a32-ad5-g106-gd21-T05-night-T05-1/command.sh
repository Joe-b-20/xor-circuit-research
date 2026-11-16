#!/bin/bash
# aes-sbox-a32-ad5-g106-gd21-T05-night-T05-1: the command recorded in the campaign sidecar (~/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad5-g106-gd21-31d6dc63b3.circ.txt, 2026-11-16T02:30:24Z).
# Repository paths are written "$REPO"; other paths ("$HOME"/...) are files of the campaign machine.
# The start circuit is logs/aes-sbox-a32-ad5-g106-gd21-T05-night-T05-1/start.circ.txt here.
# A time-budgeted search: a re-run gives a verified circuit, not necessarily this one.
# As recorded:
#   /usr/bin/python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/campaigns/targets/ops/conjpull.py --in /home/joebachir20/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad5-g106-gd23-ecfa537585.circ.txt --target T05 --seed 698471 --seconds 1100 --out /home/joebachir20/xs-campaigns/2026-11-16-night/T05/runs/T05/conjpull-31 --cap-ad 5 --schedule g:32:300,m:+0:360,m:-1:360 --repair-keep alt --conj id --cap-ad 5 --schedule m:+0:360,m:-1:360
REPO=${REPO:-$(git rev-parse --show-toplevel)}
/usr/bin/python3 "$REPO"/nonlinear/boolflux/campaigns/targets/ops/conjpull.py --in "$REPO"/nonlinear/boolflux/results/targets/T05/logs/aes-sbox-a32-ad5-g106-gd21-T05-night-T05-1/start.circ.txt --target T05 --seed 698471 --seconds 1100 --out "$HOME"/xs-campaigns/2026-11-16-night/T05/runs/T05/conjpull-31 --cap-ad 5 --schedule g:32:300,m:+0:360,m:-1:360 --repair-keep alt --conj id --cap-ad 5 --schedule m:+0:360,m:-1:360
