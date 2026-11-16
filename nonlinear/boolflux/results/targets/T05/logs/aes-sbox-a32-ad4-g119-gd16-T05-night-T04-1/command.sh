#!/bin/bash
# aes-sbox-a32-ad4-g119-gd16-T05-night-T04-1: the command recorded in the campaign sidecar (~/xs-campaigns/2026-11-16-night/T04/found/conjpull-a32-ad4-g119-gd16-3acd9d4790.circ.txt, 2026-11-16T08:12:15Z).
# Repository paths are written "$REPO"; other paths ("$HOME"/...) are files of the campaign machine.
# The start circuit is logs/aes-sbox-a32-ad4-g119-gd16-T05-night-T04-1/start.circ.txt here.
# A time-budgeted search: a re-run gives a verified circuit, not necessarily this one.
# As recorded:
#   /usr/bin/python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/campaigns/targets/ops/conjpull.py --in /home/joebachir20/xs-campaigns/2026-11-16-night/T04/found/conjpull-a32-ad4-g117-gd17-b83f9deb89.circ.txt --target T04 --seed 247057 --seconds 1260 --out /home/joebachir20/xs-campaigns/2026-11-16-night/T04/runs/T04/conjpull-677 --conj id --schedule m:-1:600,m:-1:600 --repair-keep alt
REPO=${REPO:-$(git rev-parse --show-toplevel)}
/usr/bin/python3 "$REPO"/nonlinear/boolflux/campaigns/targets/ops/conjpull.py --in "$REPO"/nonlinear/boolflux/results/targets/T05/logs/aes-sbox-a32-ad4-g119-gd16-T05-night-T04-1/start.circ.txt --target T04 --seed 247057 --seconds 1260 --out "$HOME"/xs-campaigns/2026-11-16-night/T04/runs/T04/conjpull-677 --conj id --schedule m:-1:600,m:-1:600 --repair-keep alt
