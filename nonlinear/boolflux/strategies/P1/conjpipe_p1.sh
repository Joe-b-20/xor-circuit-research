#!/bin/bash
# P1 conjugate pipeline (method of P3: GF(2^8) conjugation x -> lam*x^(2^k), outputs through the matching
# affine map; strategies/P1/conj/ = copies of P3's conj.py, mkconj.py, bottom.py with import paths fixed).
# For every line "START LAM K" of LIST: mkconj -> fdrive gate at cap G1 (S1 s) -> fdrive mix at cap D2 (S2 s)
# -> fdrive mix at cap D3 (S3 s), each stage from the previous stage's best; hard caps --cap-a 28 --cap-ad AD
# on every kernel call; every stage best recorded with p1rec.py (found/ if new, shared/ always).
#   conjpipe_p1.sh TARGET AD G1 D2 D3 S1 S2 S3 LIST
set -u
TG=$1; AD=$2; G1=$3; D2=$4; D3=$5; S1=$6; S2=$7; S3=$8; LIST=$9
P1=/home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P1
F=/home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P1
DATA=/home/joebachir20/xs-campaigns/2026-11-15-targets/P1
K=$DATA/bin/bfx-94a75e2c18
seed=1
while read -r ST LAM KK; do
  [ -z "$ST" ] && continue
  case "$ST" in \#*) continue;; esac
  B=$(basename $ST); B=${B%.circ.txt}; B=${B%.bfx}; B=${B:0:40}
  R=$DATA/runs/conj/$TG-$B-l$LAM-k$KK; mkdir -p $R
  python3 $P1/conj/mkconj.py $ST $LAM $KK $R/conj.circ.txt > $R/mkconj.out 2>&1 || { echo "mkconj failed $R"; continue; }
  echo "$(date -u +%T) $R conj: $(cat $R/mkconj.out | tail -1 | cut -d' ' -f2-)"
  prev=$R/conj.circ.txt
  for st in 1 2 3; do
    case $st in 1) MODE=gate; CAP=$G1; SEC=$S1;; 2) MODE=mix; CAP=$D2; SEC=$S2;; 3) MODE=mix; CAP=$D3; SEC=$S3;; esac
    O=$R/s$st; mkdir -p $O
    CMD="env F_BFX=$K python3 $F/fdrive_p1.py --start $prev --cap $CAP --cap-ad $AD --cap-a 28 --mode $MODE --seconds $SEC --seed $seed --out $O"
    echo "$CMD" > $O/command.txt
    T0=$(date +%s); $CMD > $O/fdrive.out 2>&1; T1=$(date +%s)
    if [ -f $O/best.circ.txt ]; then
      echo "$(date -u +%T)   s$st $MODE cap $CAP: $(python3 $P1/p1rec.py --circ $O/best.circ.txt --target $TG --start $ST \
        --method "conjugate lam $LAM k $KK of start (P3 conj/mkconj) -> fdrive stages; this stage: $MODE cap $CAP" \
        --command "$P1/conj/mkconj.py $ST $LAM $KK $R/conj.circ.txt ; stage commands in $R/s*/command.txt; this: $CMD" \
        --seed $seed --elapsed $((T1-T0)) --kernel $K 2>&1 | tail -1)"
      prev=$O/best.circ.txt
    else
      echo "$(date -u +%T)   s$st $MODE cap $CAP: no feasible best"; break
    fi
    seed=$((seed + 1))
  done
done < $LIST
echo "$(date -u +%T) done"
