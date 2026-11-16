#!/bin/bash
# aes-sbox-a35-ad3-g165-gd13-T08-M3-1: the command recorded in the campaign sidecar (~/xs-campaigns/2026-11-15-targets/M3/found/rebase-a35-ad3-g165-gd13-7e6507bb2b.circ.txt, 2026-11-16T01:19:00Z).
# Repository paths are written "$REPO"; other paths ("$HOME"/...) are files of the campaign machine.
# The start circuit is logs/aes-sbox-a35-ad3-g165-gd13-T08-M3-1/start.circ.txt here.
# A time-budgeted search: a re-run gives a verified circuit, not necessarily this one.
# As recorded:
#   cd /home/joebachir20/xcr-boolflux && python3 nonlinear/boolflux/campaigns/targets/ops/rebase.py --in /home/joebachir20/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g168-gd13-94a02642b2d6.circ.txt --target T08 --seed 52 --seconds 900 --cap 13 --stages 1 --stage-seconds 200 --out /home/joebachir20/xs-campaigns/2026-11-15-targets/M3/runs/screen/rb-t08c13c
REPO=${REPO:-$(git rev-parse --show-toplevel)}
cd "$REPO" && python3 nonlinear/boolflux/campaigns/targets/ops/rebase.py --in "$REPO"/nonlinear/boolflux/results/targets/T08/logs/aes-sbox-a35-ad3-g165-gd13-T08-M3-1/start.circ.txt --target T08 --seed 52 --seconds 900 --cap 13 --stages 1 --stage-seconds 200 --out "$HOME"/xs-campaigns/2026-11-15-targets/M3/runs/screen/rb-t08c13c
