#!/bin/bash
# L2 probe: does the pre-hub "unreachable A cap" walk (the recipe behind 32/5/104/29) still pay when
# goal E's caps (AD <= 6, GD <= 31) are added?  6 jobs of 100 s, one at a time on CPU 12, each under xsfg.
E=/home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/E
N=/home/joebachir20/xcr-boolflux/nonlinear/nist/aes-sbox
O=/home/joebachir20/xs-campaigns/2026-11-15-study/L2/probeE
mkdir -p "$O"
cd "$E"
for s in 1 2 3; do
  XS_MEM=1G /home/joebachir20/xs-campaigns/guard/xsfg H -- taskset -c 12 python3 "$E/erun.py" \
     --start "$N/aes-sbox-a32-ad5-g107-gd22-xx75-4.circ.txt" --out "$O" --tag "n107-capA31-s$s" --seed $s --seconds 100 \
     --cap-a 31 --cap-ad 6 --cap-gd 31 --objective cost,gd > "$O/n107-capA31-s$s.out" 2>&1
  XS_MEM=1G /home/joebachir20/xs-campaigns/guard/xsfg H -- taskset -c 12 python3 "$E/erun.py" \
     --start "$N/aes-sbox-a32-ad5-g107-gd22-xx75-4.circ.txt" --out "$O" --tag "n107-capA32-s$s" --seed $s --seconds 100 \
     --cap-a 32 --cap-ad 6 --cap-gd 31 --objective cost,gd > "$O/n107-capA32-s$s.out" 2>&1
done
echo done > "$O/DONE"
