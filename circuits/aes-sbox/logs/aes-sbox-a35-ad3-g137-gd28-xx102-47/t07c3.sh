#!/bin/bash
# T07 conjugate pipeline (coordinator tip; P3 conj3/mkconj used read-only; repair_keep 1 in kern.py):
#   t07c3.sh TAG START NBEST
# 1. conj3 screen of all 2040 conjugates of START (BP top + Paar bottom proxy);
# 2. for the NBEST best-scoring non-identity conjugates: mkconj (verified start, A35 AD3), kernel G-first
#    at cap GD31 (200 s), then cap GD27 from that best (2 x 200 s; start inside A35/AD3);
# 3. harvest.py saves every new (G, GD) Pareto point (A<=35, AD<=3) into P6/found/ (target T07).
set -u
TAG=$1; START=$2; NB=$3
R=<campaign archive>/2026-11-15-targets/P6/runs/c3-$TAG
P3=<checkout>/nonlinear/boolflux/strategies/P3
P6=<checkout>/nonlinear/boolflux/strategies/P6
mkdir -p $R; cd $P6
python3 $P3/conj3.py $START --out $R --top-runs 4 > $R/conj3.log 2>&1
python3 - $R $NB > $R/picks.txt <<'EOF'
import json, sys
R, nb = sys.argv[1], int(sys.argv[2])
rs = [json.loads(l) for l in open(R + '/screen3.jsonl')]
rs = [r for r in rs if not (r['lam'] == 1 and r['k'] == 0)]
rs.sort(key=lambda r: (r['sum'], r['lam'], r['k']))
for r in rs[:nb]: print(r['lam'], r['k'], r['sum'])
EOF
while read -r lam k sc; do
  C=$R/cj-$lam-$k.circ.txt
  python3 $P3/mkconj.py $START $lam $k $C >> $R/mkconj.log 2>&1 < /dev/null || continue
  python3 $P6/kern.py $C --caps 35,3,31 --seed $((lam * 8 + k)) --seconds 200 --out $R/x-$lam-$k-a/jobs > $R/x-$lam-$k-a.out 2>&1 < /dev/null
  B=$R/x-$lam-$k-a/jobs/best.bfx
  python3 $P6/kern.py $B --caps 35,3,27 --seed $((lam * 8 + k + 7)) --seconds 200 --stages 2 --out $R/x-$lam-$k-b/jobs > $R/x-$lam-$k-b.out 2>&1 < /dev/null
  echo "$(date -u +%T) lam $lam k $k score $sc: conj $(tail -1 $R/mkconj.log | awk '{print $3"/"$4"/"$5"/"$6}') cap31 $(tail -1 $R/x-$lam-$k-a.out) | cap27 $(tail -1 $R/x-$lam-$k-b.out)" >> $R/log.txt
  for d in $R/x-$lam-$k-a $R/x-$lam-$k-b; do
    python3 $P6/harvest.py $d --target T07 --command "bash <campaign archive>/2026-11-15-targets/P6/runs/t07c3.sh $TAG $START $NB (conjugate lam $lam k $k; stage dir $d)" >> $R/harvest.out 2>&1
  done
done < $R/picks.txt
