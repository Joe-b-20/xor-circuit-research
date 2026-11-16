#!/bin/bash
# aes-sbox-a28-ad5-g129-gd19-T03-P1-1: the command recorded in the campaign sidecar (~/xs-campaigns/2026-11-15-targets/P1/found/P1-T03-a28-ad5-g129-gd19-ec51e03b02b5.circ.txt, 2026-11-15T17:15:02Z).
# Repository paths are written "$REPO"; other paths ("$HOME"/...) are files of the campaign machine.
# A time-budgeted search: a re-run gives a verified circuit, not necessarily this one.
# As recorded:
#   cd /home/joebachir20/xs-campaigns/2026-11-15-targets/P1/runs/usat2 && python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P1/unionsat2.py --lns /home/joebachir20/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-pull-g130-a28-gd19-ad5.circ.txt --starts /home/joebachir20/xs-campaigns/2026-11-15-targets/P1/starts_fam.json --extra /home/joebachir20/xs-campaigns/2026-11-15-targets/P1/shared --D 19 --cap-ad 5 --seconds 900 --lns-sec 20 --seed 23 --out t03-d19-best.circ.txt --outdir t03-d19-out --log /home/joebachir20/xs-campaigns/2026-11-15-targets/P1/runs/usat2/lns2.jsonl
REPO=${REPO:-$(git rev-parse --show-toplevel)}
cd "$HOME"/xs-campaigns/2026-11-15-targets/P1/runs/usat2 && python3 "$REPO"/nonlinear/boolflux/strategies/P1/unionsat2.py --lns "$REPO"/nonlinear/boolflux/results/aes/aes-nist-hub-pull-g130-a28-gd19-ad5.circ.txt --starts "$HOME"/xs-campaigns/2026-11-15-targets/P1/starts_fam.json --extra "$HOME"/xs-campaigns/2026-11-15-targets/P1/shared --D 19 --cap-ad 5 --seconds 900 --lns-sec 20 --seed 23 --out t03-d19-best.circ.txt --outdir t03-d19-out --log "$HOME"/xs-campaigns/2026-11-15-targets/P1/runs/usat2/lns2.jsonl
