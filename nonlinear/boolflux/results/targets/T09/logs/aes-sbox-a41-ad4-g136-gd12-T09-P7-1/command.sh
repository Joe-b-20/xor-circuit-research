#!/bin/bash
# aes-sbox-a41-ad4-g136-gd12-T09-P7-1: the command recorded in the campaign sidecar (~/xs-campaigns/2026-11-15-targets/P7/found/p7-t09-a41-ad4-g136-gd12-pol-LE-p7-t09-a42-a-pw0-s9005.circ.txt, 2026-11-15T21:19:06Z).
# Repository paths are written "$REPO"; other paths ("$HOME"/...) are files of the campaign machine.
# The start circuit is logs/aes-sbox-a41-ad4-g136-gd12-T09-P7-1/start.circ.txt here.
# A time-budgeted search: a re-run gives a verified circuit, not necessarily this one.
# As recorded:
#   F_BFX=/home/joebachir20/xs-campaigns/2026-11-15-targets/P7/bin/bfx-94a75e2c18 python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P7/fdrive_p7.py --start /home/joebachir20/xs-campaigns/2026-11-15-targets/P7/runs/bopt/LE-p7-t09-a42-a-pw0-s9005.circ.txt --cap 12 --cap-ad 4 --cap-a 41 --mode gate --seconds 300.0 --seed 9005 --out /home/joebachir20/xs-campaigns/2026-11-15-targets/P7/runs/pol-LE-p7-t09-a42-a-pw0-s9005
REPO=${REPO:-$(git rev-parse --show-toplevel)}
F_BFX="$HOME"/xs-campaigns/2026-11-15-targets/P7/bin/bfx-94a75e2c18 python3 "$REPO"/nonlinear/boolflux/strategies/P7/fdrive_p7.py --start "$REPO"/nonlinear/boolflux/results/targets/T09/logs/aes-sbox-a41-ad4-g136-gd12-T09-P7-1/start.circ.txt --cap 12 --cap-ad 4 --cap-a 41 --mode gate --seconds 300.0 --seed 9005 --out "$HOME"/xs-campaigns/2026-11-15-targets/P7/runs/pol-LE-p7-t09-a42-a-pw0-s9005
