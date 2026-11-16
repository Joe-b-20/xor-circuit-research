#!/usr/bin/env python3
"""Hub campaign summary (once, or every N minutes with --every N --hours H): operator stats and the front
points produced by the campaign (not seeds).  Writes CAMPAIGN/STATUS-hub.md and prints it.

    usage: status.py CAMPAIGN [--every MINUTES --hours H]     (CAMPAIGN: the scheduler's --dir)
"""
import json, sys, time
from collections import defaultdict
from pathlib import Path

if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
    print(__doc__.strip()); sys.exit(0 if len(sys.argv) > 1 else 2)
d = Path(sys.argv[1])
if not d.is_dir():
    sys.exit('status.py: %s is not a hub campaign folder' % d)
every = float(sys.argv[sys.argv.index('--every') + 1]) if '--every' in sys.argv else 0
end = time.time() + float(sys.argv[sys.argv.index('--hours') + 1]) * 3600 if '--hours' in sys.argv else 0
while True:
    s = defaultdict(lambda: [0, 0, 0.0, 0.0])
    sf = d / 'stats.jsonl'
    for l in (sf.read_text().splitlines() if sf.exists() else []):
        x = json.loads(l); v = s[x['op']]; v[0] += 1; v[1] += x['admitted']; v[2] += x['cpu_s']; v[3] += x['gain']
    fr = json.loads((d / 'front.json').read_text()) if (d / 'front.json').exists() else []
    new = [p for p in fr if p['operator'] != 'seed']
    L = ['# hub campaign %s' % d, '', 'written %s UTC' % time.strftime('%Y-%m-%d %H:%M', time.gmtime()), '',
         '| operator | jobs | admissions | CPU s | gain | gain per CPU h |', '|---|---|---|---|---|---|']
    for k, v in sorted(s.items()):
        L.append('| %s | %d | %d | %.0f | %.2f | %.2f |' % (k, v[0], v[1], v[2], v[3], v[3] / (v[2] / 3600) if v[2] else 0))
    L += ['', 'front: %d points, %d produced by this campaign (pub_new = not dominated by the pinned NIST set):' % (len(fr), len(new))]
    for p in new:
        L.append('- %s %s pub_new=%s parents=%s run=%s' % ('/'.join(map(str, p['m'])), p['operator'], p.get('pub_new'),
                                                         ','.join(p['parents']), p.get('run_id')))
    (d / 'STATUS-hub.md').write_text('\n'.join(L) + '\n')
    if not every or time.time() > end:
        print('\n'.join(L)); break
    time.sleep(every * 60)
