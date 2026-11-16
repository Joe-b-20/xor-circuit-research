#!/bin/bash
# aes-sbox-a32-ad7-g103-gd29-T05-night-T05-1: the command recorded in the campaign sidecar (~/xs-campaigns/2026-11-16-night/T05/found/conjpull-a32-ad7-g103-gd29-8e51adc4e9.circ.txt, 2026-11-16T03:03:13Z).
# Repository paths are written "$REPO"; other paths ("$HOME"/...) are files of the campaign machine.
# A time-budgeted search: a re-run gives a verified circuit, not necessarily this one.
# As recorded:
#   /usr/bin/python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/campaigns/targets/ops/conjpull.py --in /home/joebachir20/xcr-boolflux/nonlinear/nist/aes-sbox/aes-sbox-a32-ad7-g103-gd32-xx71-10.circ.txt --target T05 --seed 775495 --seconds 1000 --out /home/joebachir20/xs-campaigns/2026-11-16-night/T05/runs/T05/conjpull-71 --schedule g:34:300,t:32:300,m:32:360 --repair-keep alt --conj rank:7
REPO=${REPO:-$(git rev-parse --show-toplevel)}
/usr/bin/python3 "$REPO"/nonlinear/boolflux/campaigns/targets/ops/conjpull.py --in "$REPO"/nonlinear/nist/aes-sbox/aes-sbox-a32-ad7-g103-gd32-xx71-10.circ.txt --target T05 --seed 775495 --seconds 1000 --out "$HOME"/xs-campaigns/2026-11-16-night/T05/runs/T05/conjpull-71 --schedule g:34:300,t:32:300,m:32:360 --repair-keep alt --conj rank:7
