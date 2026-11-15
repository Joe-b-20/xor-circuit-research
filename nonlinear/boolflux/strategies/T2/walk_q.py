#!/usr/bin/env python3
"""T2 walk: repeated gate-kernel runs (bfx, exact care-set resubstitution) under hard caps, with an
elite pool that keeps distinct circuits of equal objective so that the keys NOT in the objective
(e.g. GD under a GD cap) drift freely between jobs.  Every job's best is logged; circuits meeting a
goal are checked with campaigns/aes_check.py and copied to FOUND/ with a JSON sidecar.

  walk.py --starts F [F ...] [--archive DIR --ids ID ...] --caps A,AD,GD --objective cost
          --job-s 300 --total-s 18000 --out DIR --seed S --goal A,AD,G,GD [--found DIR]
          [--p-start 0.25] [--elite 16] [--set key=val ...]

Start files: .bfx (kernel text) or .circ.txt (NCFF).  The kernel is compiled from kernel/bfx.c into
OUT/bin (one binary per source hash).  Memory: the kernel and this driver use < 100 MB.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parents[1]
sys.path.insert(0, str(PKG.parent))
sys.path.insert(0, str(HERE))
from boolflux.hub.common import core, metrics, code_version  # noqa: E402

KDEFAULTS = {'T0': 0.6, 'Tperiod_it': 20000, 'stall_it': 60000, 'uphill': 1.0, 'max_excess': 8,
             'mv.resub1': 1, 'mv.resub2': 2, 'mv.resub3': 1, 'dmax': 220, 'pdiv': 90,
             'nl_samples': 12, 'cand_cap': 40, 'fraig': 1}
KEYW = {'cost': 'w.cost', 'g': 'w.g', 'a': 'w.a', 'gd': 'w.gd', 'ad': 'w.ad'}
MIDX = {'a': 0, 'ad': 1, 'cost': 2, 'g': 2, 'gd': 3}
AES_CHECK = PKG / 'campaigns' / 'aes_check.py'


def kernel_bin(d):
    src = PKG / 'kernel' / 'bfx.c'
    h = hashlib.sha1(src.read_bytes()).hexdigest()[:10]
    b = Path(d) / 'bin' / ('bfx-' + h)
    if not b.exists():
        b.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['gcc', '-O3', '-march=native', '-o', str(b) + '.tmp', str(src), '-lm'], check=True)
        Path(str(b) + '.tmp').rename(b)
    return b


def load(p):
    p = Path(p)
    if p.suffix == '.bfx':
        return core.from_kernel(p.read_text(), p.stem)
    return core.read_ncff(str(p))


def feasible(m, caps):
    return all(c is None or v <= c for v, c in zip((m[0], m[1], m[3]), caps))


def meets(m, goal):
    return all(g is None or v <= g for v, g in zip(m, goal))


def run_kernel(kb, c, caps, objective, seed, seconds, jd, extra):
    jd.mkdir(parents=True, exist_ok=True)
    sp = jd / 'start.bfx'; sp.write_text(core.to_kernel(c))
    bp = jd / 'best.bfx'; cp = jd / 'kernel.cfg'
    cfg = dict(KDEFAULTS)
    keys = [k.strip() for k in objective.split(',')]
    for k in KEYW.values(): cfg[k] = 0.0
    for i, k in enumerate(keys): cfg[KEYW[k]] = cfg.get(KEYW[k], 0) + 10.0 ** (-4 * i)
    cfg['lex'] = ','.join(keys)
    for op in (8, 6, 9, 3): cfg['cost.%d' % op] = 1
    for v, key in zip(caps, ('cap.a', 'cap.ad', 'cap.gd')):
        if v is not None: cfg[key] = v
    cfg.update(extra)
    cfg.update({'in': sp, 'out': bp, 'seed': seed, 'seconds': seconds})
    cp.write_text(''.join('%s %s\n' % kv for kv in cfg.items()))
    with open(jd / 'kernel.log', 'w') as lf:
        subprocess.run([str(kb), str(cp)], stdout=lf, stderr=subprocess.STDOUT)
    t_imp = None
    for ln in (jd / 'kernel.log').read_text().splitlines():
        if ln.startswith('best t '):
            try: t_imp = float(ln.split()[2])
            except ValueError: pass
    if not bp.exists(): return None, t_imp
    return core.from_kernel(bp.read_text(), 'best'), t_imp


def aes_check(path):
    r = subprocess.run([sys.executable, str(AES_CHECK), str(path)], capture_output=True, text=True)
    return r.returncode == 0, r.stdout[-3000:] + r.stderr[-1000:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--starts', nargs='*', default=[])
    ap.add_argument('--archive'); ap.add_argument('--ids', nargs='*', default=[])
    ap.add_argument('--caps', required=True); ap.add_argument('--objective', default='cost')
    ap.add_argument('--job-s', type=float, default=300); ap.add_argument('--total-s', type=float, default=3600)
    ap.add_argument('--out', required=True); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--goal', required=True); ap.add_argument('--found')
    ap.add_argument('--p-start', type=float, default=0.25); ap.add_argument('--elite', type=int, default=16)
    ap.add_argument('--keep-g', type=int, default=None, help='save every feasible distinct circuit with G <= this')
    ap.add_argument('--set', action='append', default=[])
    ap.add_argument('--alt-caps', help='relaxed caps for a share of the jobs (e.g. AD cap off); their results go to a side pool')
    ap.add_argument('--alt-job-s', type=float, default=None, help='job length for --alt-caps jobs')
    ap.add_argument('--p-alt', type=float, default=0.0, help='probability a job runs under --alt-caps (start from the main elite)')
    ap.add_argument('--p-from-alt', type=float, default=0.0, help='probability a main-caps job starts from the side pool')
    ap.add_argument('--alt-elite', type=int, default=8)
    ap.add_argument('--partial-share', type=float, default=0.0, help='share of unshare restarts that are partial (unshare_partial)')
    ap.add_argument('--chain', type=int, default=0, help='after an unshare job, continue its result for this many jobs')
    ap.add_argument('--p-unshare', type=float, default=0.0, help='probability the job start is first rebuilt by unshare.py (depth-optimal unshared XOR trees, random tie-breaks)')
    a = ap.parse_args()
    caps = tuple(None if x in ('', '-') else int(x) for x in a.caps.split(','))
    acaps = tuple(None if x in ('', '-') else int(x) for x in a.alt_caps.split(',')) if a.alt_caps else None
    goal = tuple(None if x in ('', '-') else int(x) for x in a.goal.split(','))
    extra = {}
    for s in a.set:
        k, v = s.split('=', 1); extra[k] = v
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / 'cands').mkdir(exist_ok=True)
    found = Path(a.found) if a.found else out / 'found'; found.mkdir(parents=True, exist_ok=True)
    kb = kernel_bin(out)
    keys = [k.strip() for k in a.objective.split(',')]
    starts = []
    for f in a.starts: starts.append((Path(f).name, load(f)))
    for i in a.ids: starts.append((i, core.from_kernel((Path(a.archive) / 'archive' / (i + '.bfx')).read_text(), i)))
    assert starts, 'no starts'
    rng = random.Random(a.seed)
    elite = {}            # kernel text -> (objkey, metrics, origin)
    alt = {}              # side pool: results feasible under --alt-caps only
    log = open(out / 'log.jsonl', 'a')
    cv = code_version()
    hdr = {'event': 'start', 'argv': sys.argv, 'caps': caps, 'goal': goal, 'objective': a.objective, 'code_version': cv,
           'kernel_bin': kb.name, 'starts': [s for s, _ in starts], 'start_metrics': [metrics(c) for _, c in starts],
           't': time.time()}
    log.write(json.dumps(hdr) + '\n'); log.flush()

    def okey(m):
        infeas = 0 if feasible(m, caps) else 1
        return (infeas,) + tuple(m[MIDX[k]] for k in keys)

    for name, c in starts:
        m = metrics(c)
        elite[core.to_kernel(c)] = (okey(m), m, name)
    t0 = time.time(); it = 0; best = None; seen_found = set(); follow = None
    while time.time() - t0 < a.total_s:
        it += 1
        if follow is not None and follow[1] > 0:
            c = core.from_kernel(follow[0], 'f'); origin = 'chain%d:' % follow[1] + follow[2]
            follow = (follow[0], follow[1] - 1, follow[2])
        elif rng.random() < a.p_start or not elite:
            name, c = starts[rng.randrange(len(starts))]; origin = 'start:' + name
        elif acaps and alt and rng.random() < a.p_from_alt:
            items = sorted(alt.items(), key=lambda kv: kv[1][0])
            pick = rng.choice(items[:max(1, len(items) // 2)])
            c = core.from_kernel(pick[0], 'e'); origin = 'alt:' + str(pick[1][1])
        else:
            items = sorted(elite.items(), key=lambda kv: kv[1][0])
            bestk = items[0][1][0]
            top = [kv for kv in items if kv[1][0] == bestk]
            pick = rng.choice(top) if rng.random() < 0.7 else rng.choice(items)
            c = core.from_kernel(pick[0], 'e'); origin = 'elite:' + str(pick[1][1])
        seed = a.seed * 100000 + it
        unsh = False
        if not origin.startswith('chain') and a.p_unshare and rng.random() < a.p_unshare:
            unsh = True
            import unshare as U
            if rng.random() < a.partial_share:
                c = U.unshare_partial(c, random.Random(seed)); origin = 'punshare(' + origin + ')'
            else:
                c = U.unshare(c, random.Random(seed)); origin = 'unshare(' + origin + ')'
        jd = out / 'job'
        left = a.total_s - (time.time() - t0)
        if left < 20: break
        use_alt = bool(acaps) and not origin.startswith('alt:') and rng.random() < a.p_alt
        res, t_imp = run_kernel(kb, c, acaps if use_alt else caps, a.objective, seed, min((a.alt_job_s or a.job_s) if use_alt else a.job_s, left), jd, extra)
        rec = {'alt_caps_job': use_alt, 'it': it, 'origin': origin, 'seed': seed, 'start_m': metrics(c), 't_imp': t_imp, 't': round(time.time() - t0, 1)}
        if res is None:
            rec['result'] = None; log.write(json.dumps(rec) + '\n'); log.flush(); continue
        m = metrics(res); rec['m'] = m; rec['feasible'] = feasible(m, caps)
        k = core.to_kernel(res)
        h = hashlib.sha1(k.encode()).hexdigest()[:12]; rec['id'] = h
        ok_ = okey(m)
        if rec['feasible'] and (a.keep_g is None or m[2] <= a.keep_g):
            p = out / 'cands' / ('a%d-ad%d-g%d-gd%d-%s.bfx' % (m + (h,)))
            if not p.exists(): p.write_text(k)
        if use_alt and not rec['feasible'] and feasible(m, acaps):
            if k not in alt:
                alt[k] = (okey(m)[1:], m, 'it%d' % it)
                if len(alt) > a.alt_elite:
                    items = sorted(alt.items(), key=lambda kv: kv[1][0]); del alt[items[-1][0]]
        elif k not in elite:
            elite[k] = (ok_, m, 'it%d' % it)
            if len(elite) > a.elite:
                items = sorted(elite.items(), key=lambda kv: kv[1][0])
                # keep the best; drop a random member of the worst objective class
                worst = items[-1][1][0]
                cand = [kv[0] for kv in items if kv[1][0] == worst]
                del elite[rng.choice(cand)]
        if best is None or ok_ < best: best = ok_
        rec['best'] = best
        if rec['feasible'] and meets(m, goal) and h not in seen_found:
            seen_found.add(h)
            p = found / ('T2-a%d-ad%d-g%d-gd%d-%s.bfx' % (m + (h,)))
            p.write_text(k)
            ok, txt = aes_check(p)
            side = {'file': p.name, 'metrics': {'A': m[0], 'AD': m[1], 'G': m[2], 'GD': m[3]}, 'aes_check_ok': ok,
                    'aes_check': txt, 'method': 'T2 walk.py: gate kernel bfx under caps, elite pool restarts',
                    'caps': caps, 'objective': a.objective, 'kernel_settings_extra': extra, 'seed': seed,
                    'job': it, 'origin': origin, 'start_metrics': metrics(c), 'argv': sys.argv,
                    'code_version': cv, 'kernel_bin': kb.name, 'time_utc': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())}
            (found / (p.stem + '.json')).write_text(json.dumps(side, indent=1))
            rec['found'] = p.name; rec['aes_check_ok'] = ok
            print('FOUND', p, ok, flush=True)
        if a.chain and (unsh or origin.startswith('chain')):
            if feasible(m, acaps if use_alt else caps):
                left_ = a.chain if unsh else follow[1]
                follow = (k, left_, 'it%d' % it) if left_ > 0 else None
            elif unsh:
                follow = None
        log.write(json.dumps(rec) + '\n'); log.flush()
        print(it, origin, rec['start_m'], '->', m, 'best', best, flush=True)
    log.write(json.dumps({'event': 'end', 'its': it, 'best': best, 't': time.time()}) + '\n')


if __name__ == '__main__':
    main()
