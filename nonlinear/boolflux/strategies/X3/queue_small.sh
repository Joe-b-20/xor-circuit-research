#!/bin/bash
# X3 overnight (1 CPU): from-scratch BoolFlux AND-minimisation of x^-1 in GF(32), GF(64), GF(128).
# usage: queue_small.sh CPU     Results: ~/xs-campaigns/2026-11-15-study/X3/small/gfN/ (best.circ.txt verified by the CLI)
CPU=${1:-12}
D=~/xs-campaigns/2026-11-15-study/X3/small; mkdir -p $D
cd ~/xcr-boolflux
run() { # n seeds rounds seconds
  XS_MEM=2G timeout $(( $3 * $4 * 9 + 600 )) ~/xs-campaigns/guard/xsfg H -- taskset -c $CPU \
    python3 nonlinear/boolflux/strategies/X3/bfx_custom.py pipe --target gf$1-inv --model xag --start anf \
    --objective a,cost --iters 300000 --skel-iters 300000 --seeds $2 --jobs 1 --rounds $3 --pool 4 \
    --seconds $4 --out $D/gf$1 > $D/gf$1.log 2>&1
  echo "gf$1 done $(date -u +%H:%M) $(tail -2 $D/gf$1.log | tr '\n' ' ')" >> $D/summary.txt
}
run 5 1-8 3 150
run 6 1-8 4 400
run 7 1-8 3 600
