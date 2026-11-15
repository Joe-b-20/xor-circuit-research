#!/usr/bin/env python3
"""L1 loader: read every hub-era campaign (archive records, runs, events, stats) into one cache.

    python3 l1_load.py            -> ~/xs-campaigns/2026-11-15-study/L1/cache.json

Read-only on the campaign directories.  The cache holds:
  recs   id -> archive record (union over all campaign archives; identical copies, earliest kept)
  inarch campaign -> [ids present in that campaign's archive]
  runs   campaign -> [run records, trimmed: op_info kept without 'joins'/'kernel_settings'/'tried']
  events campaign -> non-admit events
  phases long -> [(name, t0, t1)]
  published [(A, AD, G, GD)] of the pinned NIST set (hub.common.published)
"""
import json
import sys
from pathlib import Path

HOME = Path.home()
HUB = HOME / 'xs-campaigns' / '2026-11-14-hub'
import os
OUT = Path(os.environ.get('L1_OUT', str(HOME / 'xs-campaigns' / '2026-11-15-study' / 'L1')))
CAMPS = ['abhub', 'long', 'ab2base', 'ab2gen', 'ab3gen', 'ab3lin', 'ab4base', 'ab4ad3']
# other hub directories:  L1_OUT=/some/dir python3 l1_load.py name=/abs/hubdir [name2=/abs/hubdir2 ...]
# (then only these are loaded; run eval_run.py with the same L1_OUT)
EXTRA = dict(a.split('=', 1) for a in sys.argv[1:])
sys.path.insert(0, str(HOME / 'xcr-boolflux' / 'nonlinear'))


def main():
    from boolflux.hub.common import published
    recs = {}; inarch = {}; runs = {}; events = {}; stats_ts = {}
    camps = list(EXTRA) if EXTRA else CAMPS + ['main']
    for c in camps:
        d = Path(EXTRA[c]) if EXTRA else HUB / c
        ids = []
        for f in (d / 'archive').glob('*.json'):
            if f.name == 'cells.json': continue
            r = json.loads(f.read_text())
            ids.append(r['id'])
            if r['id'] not in recs or r['t_admit'] < recs[r['id']]['t_admit']:
                recs[r['id']] = r
        inarch[c] = ids
        if c == 'main': continue
        ts = {}
        sf = d / 'stats.jsonl'
        if sf.exists():
            for ln in sf.read_text().splitlines():
                s = json.loads(ln); ts[s['run_id']] = s['ts']
        rl = []
        for f in sorted((d / 'runs').glob('*.json')):
            r = json.loads(f.read_text())
            r.pop('command', None)
            oi = r.get('op_info') or {}
            ks = oi.pop('kernel_settings', None) or {}
            oi['kernel_seconds'] = ks.get('seconds')
            oi['n_joins'] = len(oi.pop('joins', None) or [])
            tr = oi.pop('tried', None)
            if isinstance(tr, list): oi['n_tried'] = len(tr); oi['tried_head'] = tr[:12]
            elif tr is not None: oi['tried'] = tr
            r['op_info'] = oi
            r['ts_end'] = ts.get(r['run_id'])
            rl.append(r)
        runs[c] = rl
        events[c] = [e for e in map(json.loads, (d / 'events.jsonl').read_text().splitlines()) if e['ev'] != 'admit']
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'cache.json').write_text(json.dumps({'camps': [c for c in camps if c != 'main'], 'recs': recs, 'inarch': inarch, 'runs': runs, 'events': events,
                                                'published': [list(p) for p in published()]}))
    print('records', len(recs), {c: len(v) for c, v in inarch.items()}, 'runs', {c: len(v) for c, v in runs.items()})


if __name__ == '__main__':
    main()
