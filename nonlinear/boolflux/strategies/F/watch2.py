#!/usr/bin/env python3
"""Quiet watch (track F): runs ~SECONDS, prints only when something needs attention:
  - a circuit anywhere in the track's campaign dirs that beats the thresholds
    (GD<=14: G<121; GD<=13: G<129; GD<=12: G<141; GD<=14 and A<=33: G<125); it is recorded
    into found/ with aes_check first (record.py), once;
  - a failed xs-F unit.
State in F/watch2.state.json.   python3 watch2.py [SECONDS]
"""
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core   # noqa: E402

F = Path.home() / 'xs-campaigns/2026-11-13-aes/F'
STATE = F / 'watch2.state.json'
DIRS = ['ab', 'pool', 'pool6', 'rep']


def qualifies(m):
    G, A, GD = m['G'], m['A'], m['GD']
    if GD <= 12 and G < 141: return 'GD12'
    if GD <= 13 and G < 129: return 'GD13'
    if GD <= 14 and G < 121: return 'GD14'
    if GD <= 14 and A <= 33 and G < 125: return 'GD14-A33'
    return None


def main():
    secs = float(sys.argv[1]) if len(sys.argv) > 1 else 165
    st = json.loads(STATE.read_text()) if STATE.exists() else {'mtimes': {}, 'done': [], 'failed': []}
    t0 = time.time(); events = []
    while time.time() - t0 < secs and not events:
        for d in DIRS:
            for bp in (F / d).glob('*/best.circ.txt'):
                k = str(bp); mt = bp.stat().st_mtime
                if st['mtimes'].get(k) == mt: continue
                st['mtimes'][k] = mt
                try:
                    c = core.read_ncff(str(bp)); m = c.metrics()
                except Exception:
                    continue
                q = qualifies(m)
                if q:
                    key = '%s|%d|%d|%d' % (k, m['G'], m['A'], m['GD'])
                    if key in st['done']: continue
                    st['done'].append(key)
                    name = 'watch-%s-%s' % (d, bp.parent.name)
                    cmdf = bp.parent / 'cmd.txt'
                    r = subprocess.run([sys.executable, str(HERE / 'record.py'), str(bp), name,
                                        '--command', cmdf.read_text().strip() if cmdf.exists() else 'see ' + str(bp.parent),
                                        '--time', 'see %s/log.jsonl or summary.json' % bp.parent,
                                        '--mechanism', 'campaign dir %s' % d], capture_output=True, text=True, timeout=900)
                    events.append('NEW %s: G=%d A=%d GD=%d AD=%d from %s\n%s' % (q, m['G'], m['A'], m['GD'], m['AD'], bp, r.stdout[-700:]))
        out = subprocess.run(['systemctl', '--user', 'list-units', '--all', '--no-legend', 'xs-F-*'],
                             capture_output=True, text=True).stdout
        for ln in out.splitlines():
            if 'failed' in ln:
                u = ln.split()[0].lstrip('●').strip() or ln.split()[1]
                if u not in st['failed']:
                    st['failed'].append(u); events.append('UNIT FAILED: ' + ln.strip())
        STATE.write_text(json.dumps(st))
        if not events: time.sleep(15)
    for e in events: print(e)


if __name__ == '__main__':
    main()
