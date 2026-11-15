#!/usr/bin/env python3
"""X2: compare campaign archives against a baseline snapshot by the user's goal list (hub/goals.py).

    python3 ab_compare.py BASE_DIR ARM_DIR [ARM_DIR ...] [--json OUT.json] [--t0 UNIX]

Per arm: per goal the best key / tuple / scalar distance (archive records, all admitted circuits), the number of
stepping-stone tuples, goal-meeting records; new Pareto-front points vs the baseline front (and vs the baseline
front + pinned NIST set), admissions, jobs and CPU-h (runs/*.json), and the time of every improvement of a goal's
best key (from record t_admit).  Reads records only (no verification; admission already verified twice)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))      # nonlinear/
from boolflux.hub import goals as GL                               # noqa: E402


def recs(d):
    out = {}
    for f in (Path(d) / 'archive').glob('*.json'):
        if f.name == 'cells.json': continue
        try:
            r = json.loads(f.read_text())
        except Exception:
            continue
        out[r['id']] = r
    return out


def tup(r):
    return (r['A'], r['AD'], r['G'], r['GD'])


def front(pts):
    pts = set(pts)
    return {p for p in pts if not any(q != p and all(a <= b for a, b in zip(q, p)) for q in pts)}


def published():
    try:
        from boolflux.hub.common import published as P
        return set(P())
    except Exception:
        return set()


def main():
    a = sys.argv[1:]; jout = None; t0 = None
    if '--json' in a: k = a.index('--json'); jout = a[k + 1]; del a[k:k + 2]
    if '--t0' in a: k = a.index('--t0'); t0 = float(a[k + 1]); del a[k:k + 2]
    base, arms = a[0], a[1:]
    B = recs(base); bpts = {tup(r) for r in B.values()}; bfront = front(bpts)
    pub = published(); bpub = front(bpts | pub)
    bst = GL.state(bpts)
    res = {'base': {'dir': base, 'records': len(B), 'front': len(bfront), 'goals': bst}}
    print('baseline %s: %d records, front %d' % (base, len(B), len(bfront)))
    for n in GL.NAMES:
        s = bst[n]; print('  %s %-28s best %s key %s scalar %s stones %d' % (n, GL.goal(n).note, s['m'], s['key'], s['scalar'], s['stones']))
    for arm in arms:
        R = recs(arm); new = {i: r for i, r in R.items() if i not in B}
        pts = {tup(r) for r in R.values()}; fr = front(pts)
        newfront = sorted(p for p in fr if p not in bfront and not any(all(x <= y for x, y in zip(q, p)) for q in bfront))
        newpub = sorted(p for p in front(pts | pub) if p not in bpub and p not in pub)
        st = GL.state(pts)
        cpu = 0.0; jobs = 0; byop = {}; bygoal = {}
        for f in (Path(arm) / 'runs').glob('*.json'):
            try:
                r = json.loads(f.read_text())
            except Exception:
                continue
            if t0 is not None and r.get('run_id') and False: pass
            jobs += 1; c = float(r.get('cpu_s') or 0); cpu += c
            o = r.get('operator'); byop.setdefault(o, [0, 0.0, 0]); byop[o][0] += 1; byop[o][1] += c; byop[o][2] += r.get('admitted', 0)
            g = r.get('goal', '-'); bygoal.setdefault(g, [0, 0.0, 0]); bygoal[g][0] += 1; bygoal[g][1] += c; bygoal[g][2] += r.get('admitted', 0)
        tl = {}
        for n in GL.NAMES:
            g = GL.goal(n); cur = bst[n]['key']; ev = []
            for r in sorted(new.values(), key=lambda r: r['t_admit']):
                k = GL.key(g, tup(r))
                if cur is None or k < cur:
                    cur = k; ev.append({'t': r['t_admit'], 'm': tup(r), 'key': k, 'id': r['id'], 'op': r['operator']})
            tl[n] = ev
        met = sorted({(n, tup(r), r['id']) for r in R.values() for n in GL.met_goals(tup(r))})
        # near-goal admissions: new records within 3 (scalar) of the baseline best, and new stepping-stone tuples
        near = {n: sum(1 for r in new.values() if GL.scalar(GL.goal(n), tup(r)) <= bst[n]['scalar'] + 3) for n in GL.NAMES}
        newstones = {n: len({tup(r) for r in new.values() if GL.stepping(GL.goal(n), tup(r))} - bpts) for n in GL.NAMES}
        res[arm] = {'records': len(R), 'new_records': len(new), 'front': len(fr), 'new_front_points': newfront,
                    'new_vs_base_and_nist': newpub, 'goals': st, 'jobs': jobs, 'cpu_h': cpu / 3600,
                    'by_op': byop, 'by_goal': bygoal, 'goal_improvements': tl, 'met': met,
                    'state_key_better_than_base': GL.state_key(st) < GL.state_key(bst), 'near3': near, 'new_stone_tuples': newstones}
        print('\narm %s: %d records (+%d), front %d, jobs %d, CPU-h %.2f' % (arm, len(R), len(new), len(fr), jobs, cpu / 3600))
        print('  new front points vs base front (%d): %s' % (len(newfront), newfront))
        print('  new vs base front + NIST (%d): %s' % (len(newpub), newpub))
        for n in GL.NAMES:
            s = st[n]; d = bst[n]
            mark = 'BETTER' if s['key'] < d['key'] else ('same' if s['key'] == d['key'] else 'worse?')
            print('  %s best %s key %s scalar %s (base %s) stones %d (base %d) %s improvements %d' % (
                n, s['m'], s['key'], s['scalar'], d['scalar'], s['stones'], d['stones'], mark, len(tl[n])))
        print('  met: %s' % (met or 'none'))
        print('  new records within 3 of the baseline best: %s' % near)
        print('  new stepping-stone tuples: %s' % newstones)
        print('  by op (jobs, cpu_s, admitted): %s' % {k: [v[0], round(v[1]), v[2]] for k, v in byop.items()})
        print('  by goal: %s' % {k: [v[0], round(v[1]), v[2]] for k, v in bygoal.items()})
    if jout: Path(jout).write_text(json.dumps(res, indent=1, default=str))


if __name__ == '__main__':
    main()
