#!/usr/bin/env bash
# Track-F event stream: new campaign bests, repair results that meet their cap, new found/ files,
# failed units (exit != 0 in logs).  One line per event.
F=$HOME/xs-campaigns/2026-11-13-aes/F
declare -A seen
snap() {
  for f in $F/ab/bests.jsonl $F/pool/bests.jsonl $F/pool6/bests.jsonl; do [ -f $f ] && wc -l < $f || echo 0; done
}
prev_found=$(ls $F/found/*.circ.txt 2>/dev/null | wc -l)
prev_rep=$(cat $F/rep/rep5.log $F/rep/rep6.log 2>/dev/null | wc -l)
prev_b=$(snap | tr '\n' ' ')
while true; do
  sleep 60
  nf=$(ls $F/found/*.circ.txt 2>/dev/null | wc -l)
  if [ "$nf" != "$prev_found" ]; then echo "found/ now $nf circuits: $(ls -t $F/found/*.circ.txt | head -n 1 | xargs basename)"; prev_found=$nf; fi
  nr=$(cat $F/rep/rep5.log $F/rep/rep6.log 2>/dev/null | wc -l)
  if [ "$nr" != "$prev_rep" ]; then
    cat $F/rep/rep5.log $F/rep/rep6.log 2>/dev/null | tail -n $((nr - prev_rep)) | grep -E "^[0-9:]+ gd13-.*GD.: 13,|^[0-9:]+ gd12-.*GD.: 12,|Traceback|Error" | cut -c1-160
    prev_rep=$nr
  fi
  nb=$(snap | tr '\n' ' ')
  if [ "$nb" != "$prev_b" ]; then tail -q -n 1 $F/ab/bests.jsonl $F/pool/bests.jsonl $F/pool6/bests.jsonl 2>/dev/null; prev_b=$nb; fi
  for u in $(systemctl --user list-units --all --no-legend 'xs-F-*' 2>/dev/null | grep -E 'failed' | awk '{print $1}'); do
    [ -z "${seen[$u]}" ] && echo "unit failed: $u" && seen[$u]=1
  done
done
