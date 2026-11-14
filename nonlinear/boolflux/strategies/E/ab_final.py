#!/usr/bin/env python3
"""Final A/B of memetic runs: per arm admissions and frontier points per CPU-hour, mechanism of each point,
time to result; aes_check (current NIST pin) on every final frontier point of every arm.

    python3 ab_final.py OUT.json NAME=RUNDIR:CPUS ...
Frontier point of an arm = admitted circuit not dominated (<= in A, AD, G, GD; equal counts) by the
published set, nor strictly dominated by another circuit of the arm's own pool (inputs + admissions).
"""
import json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import core, metrics, correct, load, MODEL, PKG   # noqa: E402
sys.path.insert(0, str(PKG / 'campaigns'))
import aes_check   # noqa: E402

FOUND = Path.home() / 'xs-campaigns/2026-11-13-aes/E/found/final'
FOUND.mkdir(parents=True, exist_ok=True)


def leq(u, m): return all(a <= b for a, b in zip(u, m))


def mech(o):
    if o.get('kind') == 'splice': return 'join'
    caps = o.get('caps') or {}
    return 'pull' if caps.get('tag') else 'polish'


pub = [u for (u, n) in aes_check.published()]
res = {}
for spec in sys.argv[2:]:
    name, rest = spec.split('=', 1); d, cpus = rest.rsplit(':', 1); d = Path(d); ncpu = int(cpus)
    ev = [json.loads(l) for l in (d / 'log.jsonl').read_text().splitlines() if l.strip()]
    t0 = ev[0]['ts']; t1 = ev[-1]['ts']; hours = (t1 - t0) / 3600
    adm_t = {}
    for e in ev:
        if e['ev'] == 'admit': adm_t[e['h']] = e['ts'] - t0
        if e['ev'] == 'polished' and e.get('admitted') and e.get('new'): adm_t[e['new']] = e['ts'] - t0
    files = (d.parent / 'files.list').read_text().split() if (d.parent / 'files.list').exists() else []
    pool = []
    for f in files:
        try:
            c = load(f)
            if correct(c): pool.append(tuple(metrics(c)))
        except Exception:
            pass
    adm = []
    for f in (d / 'admitted').glob('*.bfx'):
        c = core.from_kernel(f.read_text(), f.stem)
        o = json.loads(f.with_suffix('.json').read_text())['origin']
        adm.append({'h': f.stem, 'c': c, 'm': tuple(metrics(c)), 'o': o, 't': adm_t.get(f.stem)})
    allm = pool + [a['m'] for a in adm]
    front = []
    for a in sorted(adm, key=lambda a: a['m']):
        m = a['m']
        if any(leq(u, m) for u in pub): continue
        if any(u != m and leq(u, m) for u in allm): continue
        if any(f['m'] == m for f in front): continue
        front.append(a)
    rows = []
    for a in front:
        m = a['m']; nm = 'E-final-%s-a%d-ad%d-g%d-gd%d' % (name, *m)
        c = a['c']; c.name = nm
        nf = FOUND / (nm + '.circ.txt')
        nf.write_text(core.write_ncff(c, MODEL, comments=['Track E final frontier, arm %s, %s' % (name, json.dumps(a['o'])[:300])]))
        r = aes_check.check(str(nf))
        ok = bool(r.get('ok')) and bool(r.get('new_point'))
        (FOUND / (nm + '.json')).write_text(json.dumps({'arm': name, 'run': str(d), 'hash': a['h'], 'metrics': m,
                                                        'mechanism': mech(a['o']), 'origin': a['o'],
                                                        'admitted_after_s': a['t'], 'aes_check': {k: r.get(k) for k in ('ok', 'new_point', 'tuple', 'dominated_by')}}, indent=1) + '\n')
        rows.append({'m': m, 'mech': mech(a['o']), 't_min': round(a['t'] / 60, 1) if a['t'] is not None else None,
                     'check_ok_new': ok, 'ttr_polish_s': (a['o'].get('time_to_result_s') if a['o'].get('kind') == 'polish' else None),
                     'origin': a['o']})
    cnt = {}
    for a in adm: cnt[mech(a['o'])] = cnt.get(mech(a['o']), 0) + 1
    fcnt = {}
    for r in rows: fcnt[r['mech']] = fcnt.get(r['mech'], 0) + 1
    cpuh = hours * ncpu
    res[name] = {'run': str(d), 'hours': round(hours, 2), 'cpus': ncpu, 'cpu_h': round(cpuh, 2), 'admissions': len(adm),
                 'admissions_by_mech': cnt, 'admissions_per_cpu_h': round(len(adm) / cpuh, 2) if cpuh else None,
                 'frontier': len(rows), 'frontier_by_mech': fcnt, 'frontier_per_cpu_h': round(len(rows) / cpuh, 2) if cpuh else None,
                 'all_checked_ok_new': all(r['check_ok_new'] for r in rows),
                 'polishes': sum(1 for e in ev if e['ev'] == 'polished'), 'splice_steps': sum(1 for e in ev if e['ev'] == 'spliced'),
                 'points': rows}
    print('== %s: %.2f h x %d CPU; admissions %d %s (%.2f/CPU-h); frontier %d %s (%.2f/CPU-h); all aes_check OK+new: %s' % (
        name, hours, ncpu, len(adm), cnt, res[name]['admissions_per_cpu_h'] or 0, len(rows), fcnt, res[name]['frontier_per_cpu_h'] or 0,
        res[name]['all_checked_ok_new']))
    for r in rows:
        print('   %-14s %-6s at %5s min  check %s  %s' % ('/'.join(map(str, r['m'])), r['mech'], r['t_min'], 'OK-new' if r['check_ok_new'] else 'FAIL',
                                                      ('polish ttr %.0f s' % r['ttr_polish_s']) if r['ttr_polish_s'] else ''))
# cross-arm dominance
names = list(res)
for a in names:
    for b in names:
        if a == b: continue
        n = sum(1 for p in res[a]['points'] if not any(leq(q['m'], p['m']) for q in res[b]['points']))
        res[a].setdefault('not_dominated_by', {})[b] = n
Path(sys.argv[1]).write_text(json.dumps(res, indent=1, default=str) + '\n')
print(json.dumps({k: v.get('not_dominated_by') for k, v in res.items()}))
