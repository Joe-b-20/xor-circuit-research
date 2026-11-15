"""Summary of the track G campaigns (walk + exact evaluation records) -> markdown on stdout.

usage: python3 summarize.py [CAMPAIGN_DIR ...]   (default: ~/xs-campaigns/2026-11-14-G/camp-*)
"""
import collections
import glob
import json
import os
import sys
import time


def main():
    dirs = sys.argv[1:] or sorted(glob.glob(os.path.expanduser('~/xs-campaigns/2026-11-14-G/camp-X*')))
    print('# Track G auto summary (%s UTC)\n' % time.strftime('%Y-%m-%d %H:%M', time.gmtime()))
    found = sorted(glob.glob(os.path.expanduser('~/xs-campaigns/2026-11-14-G/found/*.circ.txt')))
    print('found/: %d circuit(s)%s\n' % (len(found), (': ' + ', '.join(os.path.basename(f) for f in found)) if found else ''))
    for d in dirs:
        print('## %s\n' % os.path.basename(d))
        walks = [json.loads(l) for l in open(os.path.join(d, 'walks.jsonl'))] if os.path.exists(os.path.join(d, 'walks.jsonl')) else []
        byt = collections.defaultdict(list)
        for w in walks: byt[w['tag'].split('-')[0]].append(w)
        for t, ws in sorted(byt.items()):
            print('* walks %s: %d runs, best score %s, layers dumped %d' % (
                t, len(ws), min((w['best'] for w in ws if w['best'] is not None), default=None), sum(w['nsol'] for w in ws)))
        ev = [json.loads(l) for l in open(os.path.join(d, 'eval.jsonl'))] if os.path.exists(os.path.join(d, 'eval.jsonl')) else []
        c = collections.Counter()
        vs = set()
        for r in ev:
            c[(r.get('K'), r.get('d'), r.get('dimU'), r.get('mid_ok'), r.get('cover', r.get('error')))] += 1
            if r.get('v16'): vs.add(tuple(r['v16']))
        print('* evaluated layers: %d (distinct middle functions v: %d)' % (len(ev), len(vs)))
        for k, n in sorted(c.items(), key=lambda kv: -kv[1])[:12]:
            print('  * %d x K=%s quad-junk=%s dimU=%s middle_ok=%s cover=%s' % ((n,) + k))
        hits = [r for r in ev if r.get('circuit')]
        print('* circuits built: %d\n' % len(hits))


if __name__ == '__main__':
    main()
