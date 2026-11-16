#!/bin/bash
# aes-sbox-a38-ad4-g135-gd12-T10-night-T09-1: the command recorded in the campaign sidecar (~/xs-campaigns/2026-11-16-night/T09/found/bottom-a38-ad4-g135-gd12-ff41a311d8.circ.txt, 2026-11-16T09:46:21Z).
# Repository paths are written "$REPO"; other paths ("$HOME"/...) are files of the campaign machine.
# The start circuit is logs/aes-sbox-a38-ad4-g135-gd12-T10-night-T09-1/start.circ.txt here.
# A time-budgeted search: a re-run gives a verified circuit, not necessarily this one.
# As recorded:
#   cd /home/joebachir20/xcr-boolflux && python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/campaigns/targets/ops/bottom.py --in /home/joebachir20/xs-campaigns/2026-11-16-night/T09/found/bottom-a39-ad4-g138-gd12-09d79a36df.circ.txt --target T09 --seed 432999 --seconds 900 --out /home/joebachir20/xs-campaigns/2026-11-16-night/T09/runs/T09/bottom-832 --init own --pw 3 --polish-seconds 300
REPO=${REPO:-$(git rev-parse --show-toplevel)}
cd "$REPO" && python3 "$REPO"/nonlinear/boolflux/campaigns/targets/ops/bottom.py --in "$REPO"/nonlinear/boolflux/results/targets/T10/logs/aes-sbox-a38-ad4-g135-gd12-T10-night-T09-1/start.circ.txt --target T09 --seed 432999 --seconds 900 --out "$HOME"/xs-campaigns/2026-11-16-night/T09/runs/T09/bottom-832 --init own --pw 3 --polish-seconds 300
