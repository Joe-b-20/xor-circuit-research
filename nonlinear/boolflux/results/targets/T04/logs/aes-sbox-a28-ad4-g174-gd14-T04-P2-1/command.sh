#!/bin/bash
# aes-sbox-a28-ad4-g174-gd14-T04-P2-1: the command recorded in the campaign sidecar (~/xs-campaigns/2026-11-15-targets/P2/found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt, 2026-11-15T16:21:12Z).
# Repository paths are written "$REPO"; other paths ("$HOME"/...) are files of the campaign machine.
# The start circuit is logs/aes-sbox-a28-ad4-g174-gd14-T04-P2-1/start.circ.txt here.
# A time-budgeted search: a re-run gives a verified circuit, not necessarily this one.
# As recorded:
#   env F_BFX=/home/joebachir20/xs-campaigns/2026-11-14-hub/long/bin/bfx-593fa798f5 python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/F/fdrive.py --start /home/joebachir20/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a28-ad4-g175-gd14-xx147-68.circ.txt --cap 14 --cap-ad 4 --cap-a 28 --mode mix --seconds 7200 --seed 1 --out /home/joebachir20/xs-campaigns/2026-11-15-targets/P2/runs/t02mix1
REPO=${REPO:-$(git rev-parse --show-toplevel)}
env F_BFX="$HOME"/xs-campaigns/2026-11-14-hub/long/bin/bfx-593fa798f5 python3 "$REPO"/nonlinear/boolflux/strategies/F/fdrive.py --start "$REPO"/nonlinear/boolflux/results/targets/T04/logs/aes-sbox-a28-ad4-g174-gd14-T04-P2-1/start.circ.txt --cap 14 --cap-ad 4 --cap-a 28 --mode mix --seconds 7200 --seed 1 --out "$HOME"/xs-campaigns/2026-11-15-targets/P2/runs/t02mix1
