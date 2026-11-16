#!/bin/bash
# aes-sbox-a32-ad4-g114-gd19-T05-P3-1: the command recorded in the campaign sidecar (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt, 2026-11-15T20:06:10Z).
# Repository paths are written "$REPO"; other paths ("$HOME"/...) are files of the campaign machine.
# The start circuit is logs/aes-sbox-a32-ad4-g114-gd19-T05-P3-1/start.circ.txt here.
# A time-budgeted search: a re-run gives a verified circuit, not necessarily this one.
# As recorded:
#   env F_BFX=/home/joebachir20/xs-campaigns/2026-11-15-targets/P3/bin/bfx-4dc199db python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P3/pdrive.py --start /home/joebachir20/xs-campaigns/2026-11-15-targets/P3/runs/rkG1-stage2.circ.txt --cap 19 --cap-ad 4 --cap-a 32 --mode mix --seconds 360 --seed 1031 --out /home/joebachir20/xs-campaigns/2026-11-15-targets/P3/runs/rkG1-s3-mix19-k1 
REPO=${REPO:-$(git rev-parse --show-toplevel)}
env F_BFX="$HOME"/xs-campaigns/2026-11-15-targets/P3/bin/bfx-4dc199db python3 "$REPO"/nonlinear/boolflux/strategies/P3/pdrive.py --start "$REPO"/nonlinear/boolflux/results/targets/T05/logs/aes-sbox-a32-ad4-g114-gd19-T05-P3-1/start.circ.txt --cap 19 --cap-ad 4 --cap-a 32 --mode mix --seconds 360 --seed 1031 --out "$HOME"/xs-campaigns/2026-11-15-targets/P3/runs/rkG1-s3-mix19-k1 
