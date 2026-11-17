#!/bin/bash
# andpull.sh HITS SECONDS SEED OUTROOT : HITS lines "file gdcap"; kernel (karm.py) per hit with GD cap = source GD
hits=$1; secs=$2; seed=$3; root=$4
export BOOLFLUX_CACHE=$HOME/xs-campaigns/2026-11-17-ideas/09/cache
mkdir -p "$root"; i=0
while read -r f gd; do
  [ -z "$f" ] && continue
  i=$((i+1)); d=$root/$(printf '%03d' $i)-$(basename "$f" .bfx)-gd$gd
  echo "$(date -u +%FT%TZ) start $f gd $gd" >> "$root/progress.log"
  python3 $HOME/xs-campaigns/2026-11-17-ideas/09/karm.py --in "$f" --seed $((seed+i)) --seconds $secs --out "$d" --gd $gd > "$d.log" 2>&1
  echo "$(date -u +%FT%TZ) end rc $?" >> "$root/progress.log"
done < "$hits"
echo "$(date -u +%FT%TZ) done" >> "$root/progress.log"
