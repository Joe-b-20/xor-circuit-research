#!/bin/bash
# cpipe4.sh START TOPN: AD4 any-GD pipeline.  conj3 screen of START (2040 conjugates), then for
# the TOPN best (lam, k) other than the identity: mkconj start, gate cap GD30 (300 s), mix cap GD26
# (400 s) from that best.  Also the identity itself (gate cap 30, mix cap 26).  One CPU.
P5=/home/joebachir20/xs-campaigns/2026-11-15-targets/P5
S=/home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P5
ST=$1; N=${2:-4}
B=$(basename $ST .circ.txt | cut -c1-40)
cd $S
SC=$P5/runs/conj3-$B
if [ ! -f $SC/screen3.jsonl ]; then python3 p3_conj3.py $ST --out $SC > $SC.log 2>&1; fi
python3 - $SC/screen3.jsonl $N > $P5/runs/cp4-$B.lams <<'EOF'
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1])]
rows = [r for r in rows if not (r['lam'] == 1 and r['k'] == 0)]
rows.sort(key=lambda r: (r['sum'], r['bot']))
for r in rows[:int(sys.argv[2])]: print(r['lam'], r['k'])
EOF
echo "$(date -u +%T) lams: $(tr '\n' ' ' < $P5/runs/cp4-$B.lams)"
run2() {   # run2 START TAG
  $S/cjob.sh $1 4 30 gate 1 300 $2-g30
  echo "$(date -u +%T) $2-g30: $(grep '"best"' $P5/runs/$2-g30/log.jsonl | tail -1 | cut -c1-80)"
  if [ -f $P5/runs/$2-g30/best.circ.txt ]; then
    cp $P5/runs/$2-g30/best.circ.txt $P5/runs/$2-g30/stage1.circ.txt
    $S/cjob.sh $P5/runs/$2-g30/stage1.circ.txt 4 26 mix 2 400 $2-m26
    echo "$(date -u +%T) $2-m26: pareto: $(ls $P5/runs/$2-m26/pareto 2>/dev/null | tr '\n' ' ')"
  fi
}
run2 $ST cp4-$B-id
while read -r L K; do
  CS=$P5/starts/$B-cj${L}k$K.circ.txt
  python3 p3_mkconj.py $ST $L $K $CS > /dev/null 2>&1 || continue
  run2 $CS cp4-$B-l${L}k$K
done < $P5/runs/cp4-$B.lams
echo DONE $(date -u +%T)
