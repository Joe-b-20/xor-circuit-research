#!/bin/bash
# T2: front walks of the NIST 117@19 at cut levels 3 then 2 (per-output deadlines for GD 19)
FW=$HOME/xcr-boolflux/nonlinear/boolflux/strategies/T2/frontwalk.py
AR=$HOME/xs-campaigns/2026-11-14-hub/long
D=$HOME/xs-campaigns/2026-11-15-study/T2
S="073a719e1bc5 a43e1ae3d73f 33e0003e3b49 8a0d890de9f4 9e4ddc8a4a29 79bccd2434fd 5d3e9d8c8e91 85688e53fda2 51a5202c2d97 20b1d351cfa9"
python3 $FW --archive $AR --y 073a719e1bc5 --ly 3 --cap 19 --starts $S --job-s 180 --total-s 2700 --out $D/dfront3 --goal 32,4,116,19 --found $D/found --seed 33
python3 $FW --archive $AR --y 073a719e1bc5 --ly 2 --cap 19 --starts $S --job-s 150 --total-s 2400 --out $D/dfront2 --goal 32,4,116,19 --found $D/found --seed 32
