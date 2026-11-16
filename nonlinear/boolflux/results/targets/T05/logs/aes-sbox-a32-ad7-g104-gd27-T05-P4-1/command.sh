#!/bin/bash
# aes-sbox-a32-ad7-g104-gd27-T05-P4-1: the command recorded in the campaign sidecar (~/xs-campaigns/2026-11-15-targets/P4/found/p4-deep236-a32-ad7-g104-gd27.circ.txt, 2026-11-15T18:51:33Z).
# Repository paths are written "$REPO"; other paths ("$HOME"/...) are files of the campaign machine.
# The start circuit is logs/aes-sbox-a32-ad7-g104-gd27-T05-P4-1/start.circ.txt here.
# A time-budgeted search: a re-run gives a verified circuit, not necessarily this one.
# As recorded:
#   env F_BFX=/home/joebachir20/xs-campaigns/2026-11-15-targets/P4/bin/bfx-94a75e2c18 python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P4/pdrive.py --start /home/joebachir20/xs-campaigns/2026-11-15-targets/P4/runs/conj/deep-l236-r1-gate/best.circ.txt --cap 31 --relax 1 --cap-ad 7 --cap-a 32 --mode mix --seconds 600 --seed 2363 --out /home/joebachir20/xs-campaigns/2026-11-15-targets/P4/runs/conj/deep-l236-r2-mix
REPO=${REPO:-$(git rev-parse --show-toplevel)}
env F_BFX="$HOME"/xs-campaigns/2026-11-15-targets/P4/bin/bfx-94a75e2c18 python3 "$REPO"/nonlinear/boolflux/strategies/P4/pdrive.py --start "$REPO"/nonlinear/boolflux/results/targets/T05/logs/aes-sbox-a32-ad7-g104-gd27-T05-P4-1/start.circ.txt --cap 31 --relax 1 --cap-ad 7 --cap-a 32 --mode mix --seconds 600 --seed 2363 --out "$HOME"/xs-campaigns/2026-11-15-targets/P4/runs/conj/deep-l236-r2-mix
