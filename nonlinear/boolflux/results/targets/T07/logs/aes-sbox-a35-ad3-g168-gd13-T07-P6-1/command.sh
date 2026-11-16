#!/bin/bash
# aes-sbox-a35-ad3-g168-gd13-T07-P6-1: the command recorded in the campaign sidecar (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g168-gd13-94a02642b2d6.circ.txt, 2026-11-15T22:05:19Z).
# Repository paths are written "$REPO"; other paths ("$HOME"/...) are files of the campaign machine.
# The start circuit is logs/aes-sbox-a35-ad3-g168-gd13-T07-P6-1/start.circ.txt here.
# A time-budgeted search: a re-run gives a verified circuit, not necessarily this one.
# As recorded:
#   pullrun.py --parents /home/joebachir20/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g170-gd13-b418123e66e8.circ.txt /home/joebachir20/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g171-gd13-462cb948a761.circ.txt  --cap 13 --out /home/joebachir20/xs-campaigns/2026-11-15-targets/P6/runs/pull13c --builds 51 --top 3 --seconds 240 --stages 1 --seed 1391 --hours 1.0 --paar --evolve 2
REPO=${REPO:-$(git rev-parse --show-toplevel)}
pullrun.py --parents "$HOME"/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g170-gd13-b418123e66e8.circ.txt "$HOME"/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g171-gd13-462cb948a761.circ.txt  --cap 13 --out "$HOME"/xs-campaigns/2026-11-15-targets/P6/runs/pull13c --builds 51 --top 3 --seconds 240 --stages 1 --seed 1391 --hours 1.0 --paar --evolve 2
