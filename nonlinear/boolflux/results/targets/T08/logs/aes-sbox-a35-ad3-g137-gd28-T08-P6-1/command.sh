#!/bin/bash
# aes-sbox-a35-ad3-g137-gd28-T08-P6-1: the command recorded in the campaign sidecar (~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g137-gd28-23cf4c3c29d2.circ.txt, 2026-11-15T23:08:44Z).
# Repository paths are written "$REPO"; other paths ("$HOME"/...) are files of the campaign machine.
# The start circuit is logs/aes-sbox-a35-ad3-g137-gd28-T08-P6-1/start.circ.txt here.
# A time-budgeted search: a re-run gives a verified circuit, not necessarily this one.
# As recorded:
#   bash /home/joebachir20/xs-campaigns/2026-11-15-targets/P6/runs/t07c3.sh 139b /home/joebachir20/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g139-gd25-107a7c3b5078.circ.txt 8 (conjugate lam 189 k 0; stage dir /home/joebachir20/xs-campaigns/2026-11-15-targets/P6/runs/c3-139b/x-189-0-a)
REPO=${REPO:-$(git rev-parse --show-toplevel)}
bash "$HOME"/xs-campaigns/2026-11-15-targets/P6/runs/t07c3.sh 139b "$HOME"/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g139-gd25-107a7c3b5078.circ.txt 8 (conjugate lam 189 k 0; stage dir "$HOME"/xs-campaigns/2026-11-15-targets/P6/runs/c3-139b/x-189-0-a)
