#!/bin/bash
# z_status.sh [TAG] -- queue log, the current run's .out, its bound progress and subsolver header, memory
cd ~/xs-campaigns/2026-11-07-sprint/d4c2 || exit 1
date -u
cat r1.log 2>/dev/null | grep -E '^(START|EXIT|QUEUE|STOP)|status|!!!!!|MAXRSS'
for q in r2.log r3.log r4.log; do [ -e $q ] && { echo "== $q"; grep -E '^(START|EXIT|QUEUE|STOP)|status|!!!!!|MAXRSS' $q; }; done
TAG=$1
if [ -z "$TAG" ]; then TAG=$(ls -t e3_*.log 2>/dev/null | head -1 | sed 's/^e3_//; s/\.log$//'); fi
[ -n "$TAG" ] || exit 0
echo "== tag $TAG"
[ -e "e3_$TAG.out" ] && grep -v '^$' "e3_$TAG.out" | tail -6
if [ -e "e3_$TAG.log" ]; then
  grep -E 'full problem subsolvers|^#Model|presolved|incomplete subsolvers' "e3_$TAG.log" | head -6
  grep -E '^#(Bound|Done|[0-9]+ )' "e3_$TAG.log" | awk '{print $1, $2, $3, $4, $5, $6, $7}' | tail -${2:-12}
fi
ps -o pid,etime,rss,pcpu,args -C python3 | grep e3_run | grep -v grep
free -g | head -2
ls found
