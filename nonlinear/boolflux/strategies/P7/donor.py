#!/usr/bin/env python3
"""P7: mark found/ sidecars whose lineage uses a donor circuit outside the T09 limits (front reuse)."""
import json, glob
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import p7job
R = Path.home() / 'xs-campaigns/2026-11-15-targets/P7/runs/bopt'
NOTE = ('bbuild.py reads the donor file only as a gate source: it copies the fan-in cone of the donor\'s four base '
        'Y-forms (the front, %d ANDs, AD3) and assembles front + new bottom once; the only complete circuits it holds '
        'are the donor as read from disk and its single output (the cone of the new outputs, A and AD checked = %s), '
        'no intermediate complete circuit is evaluated, retained or written; bopt.py builds no circuit (tensor model only); '
        'later kernel polishes start from that output, inside A<=45/AD<=4.')


def donor_of(start):
    p = Path(start)
    if p.parent == R:
        plan = R / (p.name.replace('.circ.txt', '').replace('-v3', '') + '.json')
        if plan.exists():
            return json.load(open(plan))['circuit'], p
    return None, None


for f in sorted(glob.glob(str(Path.home() / 'xs-campaigns/2026-11-15-targets/P7/found/*.json'))):
    d = json.load(open(f)); st = d['start']['path']
    if 'donor_outside_limits' in d: continue
    don, build = (st, None) if 'a48' in Path(st).name else donor_of(st)
    if don and 'a48' in Path(don).name:
        A, AD, G, GD = p7job.metr(don)
        fr = 16
        b = build if build else Path(d['file'])
        bA = p7job.metr(str(b))
        d['donor_outside_limits'] = don
        d['donor_note'] = NOTE % (fr, '%d/%d' % (bA[0], bA[1]))
        json.dump(d, open(f, 'w'), indent=1); open(f, 'a').write('\n')
        print(Path(f).name, 'donor', Path(don).name, 'build', bA)
