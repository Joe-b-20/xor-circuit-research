#!/bin/bash
# aes-sbox-a32-ad4-g112-gd21-T04-M4-1: the command recorded in the campaign sidecar (~/xs-campaigns/2026-11-15-targets/M4/found/satlns-a32-ad4-g112-gd21-efda23263f.circ.txt, 2026-11-16T00:38:13Z).
# Repository paths are written "$REPO"; other paths ("$HOME"/...) are files of the campaign machine.
# The start circuit is logs/aes-sbox-a32-ad4-g112-gd21-T04-M4-1/start.circ.txt here.
# A time-budgeted search: a re-run gives a verified circuit, not necessarily this one.
# As recorded:
#   cd /home/joebachir20/xcr-boolflux && python3 nonlinear/boolflux/campaigns/targets/ops/satlns.py --in /home/joebachir20/xs-campaigns/2026-11-15-targets/P3/found/p3-rkG1-s1-mix21-k1-a32-ad4-g113-gd20-6a349e2eb2.circ.txt --target T04 --gd 21 --seconds 780 --out /home/joebachir20/xs-campaigns/2026-11-15-targets/M4/runs/screen/r2-t04-d21 --no-index-update --seed 23 --polish-every 40 --polish-sec 10
REPO=${REPO:-$(git rev-parse --show-toplevel)}
cd "$REPO" && python3 nonlinear/boolflux/campaigns/targets/ops/satlns.py --in "$REPO"/nonlinear/boolflux/results/targets/T04/logs/aes-sbox-a32-ad4-g112-gd21-T04-M4-1/start.circ.txt --target T04 --gd 21 --seconds 780 --out "$HOME"/xs-campaigns/2026-11-15-targets/M4/runs/screen/r2-t04-d21 --no-index-update --seed 23 --polish-every 40 --polish-sec 10
