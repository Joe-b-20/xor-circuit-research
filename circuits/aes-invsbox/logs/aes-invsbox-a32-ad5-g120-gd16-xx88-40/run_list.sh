#!/bin/bash
# run_list.sh ARM LIST SECONDS SEED OUTROOT [extra winsat flags]
#   ARM = winsat | kernel | calib ; LIST = file of start paths; one job per start, sequential.
arm=$1; list=$2; secs=$3; seed=$4; root=$5; shift 5
export BOOLFLUX_CACHE=$HOME/xs-campaigns/2026-11-17-ideas/09/cache
WT=$HOME/xcr-idea-09/search/nonlinear/boolflux
mkdir -p "$root"
i=0
while read -r f; do
  [ -z "$f" ] && continue
  i=$((i+1)); name=$(basename "$f" .circ.txt)
  d=$root/$(printf '%03d' $i)-$name
  echo "$(date -u +%FT%TZ) start $arm $name" >> "$root/progress.log"
  case $arm in
    winsat) python3 $WT/ops/winsat.py --in "$f" --target "$f" --seed $((seed+i)) --seconds $secs --out "$d" "$@" > "$d.log" 2>&1 ;;
    calib)  python3 $WT/ops/winsat.py --in "$f" --target "$f" --seed $((seed+i)) --seconds $secs --out "$d" --calib "$@" > "$d.log" 2>&1 ;;
    kernel) python3 $HOME/xs-campaigns/2026-11-17-ideas/09/karm.py --in "$f" --seed $((seed+i)) --seconds $secs --out "$d" > "$d.log" 2>&1 ;;
  esac
  echo "$(date -u +%FT%TZ) end $arm $name rc $?" >> "$root/progress.log"
done < "$list"
echo "$(date -u +%FT%TZ) done" >> "$root/progress.log"
