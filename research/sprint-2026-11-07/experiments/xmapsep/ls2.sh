cd ~/xs-campaigns/2026-11-07-sprint
for d in x1/runs/x1a x1/runs/x1b predtest/runs/pt1 predtest/runs/pt2 sweep/runs/sw1 sweep/runs/sw2; do
  echo "== $d"; ls $d | head -20
  echo "-- workers:"; ls $d/workers 2>/dev/null | head -40
done
w=$(ls -d sweep/runs/sw1/workers/* | head -1)
echo "== one worker dir: $w"; ls -la $w
echo "== events head"; head -c 2500 $w/events.jsonl; echo
echo "== event types"; python3 -c "
import json,sys,collections
c=collections.Counter()
for l in open(sys.argv[1]):
    try: e=json.loads(l)
    except Exception: continue
    c[e.get('event') or e.get('type') or e.get('kind')]+=1
print(c)
" $w/events.jsonl
echo "== improve events sample"; grep -m3 improve $w/events.jsonl
echo "== records dir"; ls sweep/runs/sw1/records 2>/dev/null | head; ls sweep/runs/sw1 | head -30
