#!/bin/bash
# aes-sbox-a32-ad4-g111-gd25-T05-P5-1: the command recorded in the campaign sidecar (~/xs-campaigns/2026-11-15-targets/P5/found/p5-lin-cert111-r1-gate30-a32-ad4-g111-gd25-5c9bbcf3c4.circ.txt, 2026-11-15T19:50:15Z).
# Repository paths are written "$REPO"; other paths ("$HOME"/...) are files of the campaign machine.
# The start circuit is logs/aes-sbox-a32-ad4-g111-gd25-T05-P5-1/start.circ.txt here.
# A time-budgeted search: a re-run gives a verified circuit, not necessarily this one.
# As recorded:
#   env F_BFX=/home/joebachir20/xs-campaigns/2026-11-14-hub/long/bin/bfx-94a75e2c18 python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P5/p3_pdrive.py --start /home/joebachir20/xs-campaigns/2026-11-15-targets/P5/starts/ad4-111-25-cert.circ.txt --cap 30 --cap-ad 4 --cap-a 32 --mode gate --seconds 300 --seed 91 --out /home/joebachir20/xs-campaigns/2026-11-15-targets/P5/runs/lin-cert111-r1-gate30
REPO=${REPO:-$(git rev-parse --show-toplevel)}
env F_BFX="$HOME"/xs-campaigns/2026-11-14-hub/long/bin/bfx-94a75e2c18 python3 "$REPO"/nonlinear/boolflux/strategies/P5/p3_pdrive.py --start "$REPO"/nonlinear/boolflux/results/targets/T05/logs/aes-sbox-a32-ad4-g111-gd25-T05-P5-1/start.circ.txt --cap 30 --cap-ad 4 --cap-a 32 --mode gate --seconds 300 --seed 91 --out "$HOME"/xs-campaigns/2026-11-15-targets/P5/runs/lin-cert111-r1-gate30
