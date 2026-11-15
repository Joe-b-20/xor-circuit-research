#!/usr/bin/env python3
"""Harvest a hub directory: every archived circuit that is not dominated by the reference archive
(default: the long hub archive) nor by the pinned NIST set is written as NCFF to FOUND/ with a JSON
sidecar and checked with campaigns/aes_check.py (two verifiers, all 256 inputs).  Goal hits (user goals
B-G of BRIEF-ADDENDUM-0135) are flagged in the sidecar and listed in FOUND/GOALS-MET.txt.

    python3 harvest.py --dir HUBDIR --found FOUNDDIR [--ref REF_ARCHIVE_DIR]

Read-only on HUBDIR and REF.  Safe to run repeatedly (files are rewritten).
"""
import argparse
import json
import sys
import time
from pathlib import Path

HOME = Path.home()
PKG = Path(__file__).resolve().parents[2]            # nonlinear/boolflux
sys.path.insert(0, str(PKG.parent)); sys.path.insert(0, str(PKG / 'campaigns'))
from boolflux import core                                 # noqa: E402
from boolflux.hub.common import MODEL, published, leq     # noqa: E402
import aes_check                                          # noqa: E402

GOALS = [('B', 28, 4, 130, 22), ('C', 28, 5, 127, 19), ('D', 32, 4, 116, 19), ('E', 32, 6, 102, 31),
         ('F', 35, 3, 138, 26), ('G', 44, 4, 140, 11)]


def recs(d):
    out = {}
    for f in Path(d).glob('*.json'):
        if f.name == 'cells.json': continue
        r = json.loads(f.read_text()); out[r['id']] = r
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', required=True); ap.add_argument('--found', required=True)
    ap.add_argument('--ref', default=str(HOME / 'xs-campaigns/2026-11-14-hub/long/archive'))
    a = ap.parse_args()
    arch = Path(a.dir) / 'archive'; found = Path(a.found); found.mkdir(parents=True, exist_ok=True)
    R = recs(arch); ref = recs(a.ref)
    base = [tuple(p) for p in published()] + [(r['A'], r['AD'], r['G'], r['GD']) for r in ref.values()]
    mine = {i: (r['A'], r['AD'], r['G'], r['GD']) for i, r in R.items() if i not in ref}
    new = {i: m for i, m in mine.items() if not any(leq(q, m) for q in base)}
    new = {i: m for i, m in new.items() if not any(q != m and leq(q, m) for q in new.values())}
    seen = set(); hits = []; n_ok = 0
    for i, m in sorted(new.items(), key=lambda kv: (kv[1], R[kv[0]]["t_admit"])):
        if m in seen: continue
        seen.add(m)
        c = core.from_kernel((arch / (i + '.bfx')).read_text(), 'L1-focus-a%d-ad%d-g%d-gd%d' % m)
        f = found / ('L1-focus-a%d-ad%d-g%d-gd%d.circ.txt' % m)
        f.write_text(core.write_ncff(c, MODEL, comments=['hub id %s, operator %s, run %s' % (i, R[i]['operator'], R[i].get('run_id'))]))
        chk = aes_check.check(str(f))
        met = [g[0] for g in GOALS if m[0] <= g[1] and m[1] <= g[2] and m[2] <= g[3] and m[3] <= g[4]]
        side = {'id': i, 'metrics': list(m), 'hub_dir': str(a.dir), 'record': R[i], 'goals_met': met,
                'aes_check': {k: chk.get(k) for k in ('ok', 'new_point', 'tuple', 'errors')}, 'harvested': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}
        f.with_suffix('').with_suffix('.json').write_text(json.dumps(side, indent=1, default=str))
        n_ok += bool(chk.get('ok'))
        if met and chk.get('ok'): hits.append('%s  goals %s  %s' % ('/'.join(map(str, m)), ','.join(met), f))
        print('%s %s %s' % ('OK  ' if chk.get('ok') else 'FAIL', '/'.join(map(str, m)), ('GOAL ' + ','.join(met)) if met else ''))
    (found / 'GOALS-MET.txt').write_text('\n'.join(hits) + ('\n' if hits else ''))
    print('records %d, not in reference %d, new non-dominated tuples %d, aes_check OK %d, goal hits %d' % (len(R), len(mine), len(seen), n_ok, len(hits)))


if __name__ == '__main__':
    main()
