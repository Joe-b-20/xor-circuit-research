#!/bin/bash
# aes-sbox-a32-ad4-g117-gd17-T05-P3-1: the command recorded in the campaign sidecar (~/xs-campaigns/2026-11-15-targets/P3/found/p3-rkN1-s1-mix17-k2-a32-ad4-g117-gd17-99c3bf2a3e.circ.txt, 2026-11-15T22:13:09Z).
# Repository paths are written "$REPO"; other paths ("$HOME"/...) are files of the campaign machine.
# The start circuit is logs/aes-sbox-a32-ad4-g117-gd17-T05-P3-1/start.circ.txt here.
# A time-budgeted search: a re-run gives a verified circuit, not necessarily this one.
# As recorded:
#   env F_BFX=/home/joebachir20/xs-campaigns/2026-11-15-targets/P3/bin/bfx-4dc199db python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P3/pdrive.py --start /home/joebachir20/xs-campaigns/2026-11-15-targets/P3/runs/rkK1-s2-mix17-k1/pareto/g118-gd17.circ.txt --cap 17 --cap-ad 4 --cap-a 32 --mode mix --seconds 600 --seed 2212 --out /home/joebachir20/xs-campaigns/2026-11-15-targets/P3/runs/rkN1-s1-mix17-k2 
REPO=${REPO:-$(git rev-parse --show-toplevel)}
env F_BFX="$HOME"/xs-campaigns/2026-11-15-targets/P3/bin/bfx-4dc199db python3 "$REPO"/nonlinear/boolflux/strategies/P3/pdrive.py --start "$REPO"/nonlinear/boolflux/results/targets/T05/logs/aes-sbox-a32-ad4-g117-gd17-T05-P3-1/start.circ.txt --cap 17 --cap-ad 4 --cap-a 32 --mode mix --seconds 600 --seed 2212 --out "$HOME"/xs-campaigns/2026-11-15-targets/P3/runs/rkN1-s1-mix17-k2 
