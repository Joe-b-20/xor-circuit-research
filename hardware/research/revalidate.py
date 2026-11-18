#!/usr/bin/env python3
"""Revalidate cached research jobs after a change of harness.py (-> results/revalidation.json).

    python3 hardware/research/revalidate.py [--dry-run] [-j 12]
    python3 hardware/research/revalidate.py --record-reruns     # after run.py reran the superseded jobs

A research job's fingerprint includes harness.py's SHA-256 and the variant's settings, so after
any change of the harness every cached job is stale.  Rather than rerun them all, this script
checks each one against what the current harness would give it, and re-stamps it only if all of
these are byte-identical:

  rtl.v        the circuit's RTL (statement order of the variant)
  synthesis    synth.ys and abc.constr / cellmap.v, and mapped.v: Yosys + ABC are run again in
               build/_revalidate/ and their netlist (instance order of the variant) compared
  pnr.tcl      the OpenROAD script (placement setting of the variant)
  sdc          constraints.sdc

and the job's old fingerprint is the benchmark's fingerprint of the same job under the current
benchmark code and tools (so nothing else changed).  The re-stamped metrics.json keeps its
numbers and gets the new fingerprint, ``fingerprint_before`` and a research record saying how it
was revalidated.  A job that fails a comparison is moved, whole, to build/_superseded/<variant>/
(its numbers are kept in revalidation.json) and is rerun by run.py; --record-reruns then adds
the rerun's numbers next to the old ones.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime
import json
import os
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import harness as H  # noqa: E402
import manifest as M  # noqa: E402
from hwbench import design as D, flow as F, liberty as L, platforms as P, verilog as V  # noqa: E402

TMP = H.RBUILD / '_revalidate'
SUPERSEDED = H.RBUILD / '_superseded'
CHECKED = ['old fingerprint = benchmark fingerprint under the current benchmark code and tools',
           'rtl.v', 'synth.ys', 'abc.constr or cellmap.v', 'mapped.v (Yosys + ABC rerun)',
           'pnr.tcl', 'constraints.sdc']
NOW = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def _design(args):
    """RTL of a (variant, circuit): 'ok' (already current), 'restamp', or a reason."""
    variant, path, dry = args
    H.set_variant(variant)
    d = D.load(path)
    f = F.design_dir(d) / 'rtl_check.json'
    if not f.exists():
        return 'no rtl_check.json'
    rc = json.loads(f.read_text())
    if rc.get('fingerprint') == H.job_fingerprint(variant, d.sha256):
        return 'ok'
    if rc.get('fingerprint') != H.bench_fingerprint(d.sha256):
        return 'rtl_check.json fingerprint is not the benchmark fingerprint'
    if (F.design_dir(d) / 'rtl.v').read_text() != V.rtl(d):
        return 'rtl.v differs'
    if not dry:
        rc['fingerprint'] = H.job_fingerprint(variant, d.sha256)
        rc['revalidated'] = NOW
        f.write_text(json.dumps(rc) + '\n')
    return 'restamp'


def _same(a, b):
    return a.exists() and b.exists() and a.read_bytes() == b.read_bytes()


def _job(args):
    variant, path, plat, flow, dry = args
    H.set_variant(variant)
    d = D.load(path)
    p = P.get(plat)
    out = F.job_dir(d, plat, flow)
    mf = out / 'metrics.json'
    key = '%s|%s|%s|%s' % (variant, d.id, plat, flow)
    if not mf.exists():
        return key, 'missing', None, None
    r = json.loads(mf.read_text())
    parts = (d.sha256, plat, flow, H.lib_sha(plat))
    new = H.job_fingerprint(variant, *parts)
    if r.get('fingerprint') == new and (r.get('research') or {}).get('settings') == H.settings(variant):
        return key, 'ok', None, None
    old = H.bench_fingerprint(*parts)
    bad = []
    if r.get('fingerprint') != old:
        bad.append('old fingerprint %s is not the benchmark fingerprint %s' % (r.get('fingerprint'), old))
    if (F.design_dir(d) / 'rtl.v').read_text() != V.rtl(d):
        bad.append('rtl.v')
    tmp = TMP / variant / d.id / plat / flow
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    lib = L.load(p.path(p.lib), cache_dir=F.BUILD / '_liberty')
    try:
        F.synth(d, p, flow, tmp, lib)
    except Exception as e:                       # noqa: BLE001
        bad.append('synthesis rerun failed: %s' % str(e)[:200])
    side = 'cellmap.v' if flow == 'preserve' else 'abc.constr'
    for name in ('synth.ys', side, 'mapped.v'):
        if not _same(out / name, tmp / name):
            bad.append(name)
    real = F.tool
    F.tool = lambda *a, **k: ''                  # write pnr.tcl only
    try:
        F.pnr(p, tmp, lib)
    finally:
        F.tool = real
    if not _same(out / 'pnr.tcl', tmp / 'pnr.tcl'):
        bad.append('pnr.tcl')
    if (out / 'constraints.sdc').read_text() != F.sdc(p, lib):
        bad.append('constraints.sdc')
    shutil.rmtree(tmp)
    nums = {'area_um2': r['area_um2'], 'delay_ns': r['route']['delay_ns'],
            'adp_um2ns': r['route']['adp_um2ns'], 'power_W': r['route']['power']['total_W'],
            'fingerprint': r.get('fingerprint')}
    if bad:
        if not dry:
            dest = SUPERSEDED / variant / d.id / plat / flow
            if dest.exists():
                shutil.rmtree(dest)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(out), str(dest))
        return key, 'superseded', bad, nums
    if not dry:
        r['fingerprint_before'] = r['fingerprint']
        r['fingerprint'] = new
        r['research'] = H.record(variant, run='before 2026-11-18, by the harness of commit 9650abd '
                                 '(fingerprints without the harness)',
                                 revalidated={'date': NOW, 'by': 'revalidate.py', 'checked': CHECKED})
        mf.write_text(json.dumps(r, indent=1, sort_keys=True) + '\n')
    return key, 'restamped', None, nums


def record_reruns():
    out = HERE / 'results' / 'revalidation.json'
    data = json.loads(out.read_text())
    for run in data['runs']:
        for key, e in run.get('superseded', {}).items():
            variant, design, plat, flow = key.split('|')
            mf = H.RBUILD / variant / design / plat / flow / 'metrics.json'
            if not mf.exists():
                print('not rerun yet:', key)
                continue
            r = json.loads(mf.read_text())
            e['after'] = {'area_um2': r['area_um2'], 'delay_ns': r['route']['delay_ns'],
                          'adp_um2ns': r['route']['adp_um2ns'],
                          'power_W': r['route']['power']['total_W'],
                          'fingerprint': r['fingerprint']}
            e['change'] = {k: e['after'][k] / e['before'][k] - 1
                           for k in ('area_um2', 'delay_ns', 'adp_um2ns', 'power_W')}
            print(key, {k: '%+.2f%%' % (100 * v) for k, v in e['change'].items()})
    out.write_text(json.dumps(data, indent=1, sort_keys=True) + '\n')
    return 0


REPRO = H.RBUILD / '_reproduce'
NUMS = ('area_um2', 'cells', 'delay_ns', 'route.delay_ns', 'route.adp_um2ns', 'route.power.total_W',
        'route.wirelength_um', 'stages.place.delay_ns')


def _get(r, k):
    for part in k.split('.'):
        r = r[part]
    return r


def _reproduce(args):
    """Rerun a job from scratch in build/_reproduce/ and compare its numbers with the cached ones."""
    variant, path, plat, flow = args
    H.set_variant(variant)
    d = D.load(path)
    cached = json.loads((F.job_dir(d, plat, flow) / 'metrics.json').read_text())
    F.BUILD = REPRO / variant           # emptied once by reproduce(); jobs of a circuit share it
    try:
        r = F.run_job(path, plat, flow, force=True)
    except Exception as e:                       # noqa: BLE001
        return '%s|%s|%s|%s' % (variant, d.id, plat, flow), {'error': str(e)[:300]}
    diff = {k: [_get(cached, k), _get(r, k)] for k in NUMS if _get(cached, k) != _get(r, k)}
    return '%s|%s|%s|%s' % (variant, d.id, plat, flow), diff


def reproduce(n, jobs, stages, seed=20261118):
    """Rerun n jobs drawn with a fixed seed (G < 400) and record whether every number repeats."""
    import random
    js = [j for j in M.jobs(stages) if j.variant is not None and j.design().metrics['G'] < 400]
    pick = random.Random(seed).sample(js, min(n, len(js)))
    res = {'date': NOW, 'seed': seed, 'stages': list(stages), 'population': 'research jobs with G < 400',
           'n': len(pick), 'compared': list(NUMS), 'identical': 0, 'differing': {},
           'jobs': sorted('%s|%s|%s|%s' % (j.variant, j.design().id, j.platform, j.flow) for j in pick)}
    if REPRO.exists():
        shutil.rmtree(REPRO)
    with cf.ProcessPoolExecutor(jobs) as ex:
        for key, diff in ex.map(_reproduce, [(j.variant, j.file, j.platform, j.flow) for j in pick]):
            if diff:
                res['differing'][key] = diff
                print('DIFFERS', key, diff, flush=True)
            else:
                res['identical'] += 1
    print('reproduced %d jobs: %d identical, %d differing' % (res['n'], res['identical'],
                                                              len(res['differing'])))
    out = HERE / 'results' / 'revalidation.json'
    data = json.loads(out.read_text()) if out.exists() else {'runs': []}
    data.setdefault('reproduced', []).append(res)
    out.write_text(json.dumps(data, indent=1, sort_keys=True) + '\n')
    shutil.rmtree(REPRO)
    return 1 if res['differing'] else 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('-j', '--jobs', type=int, default=os.cpu_count())
    ap.add_argument('--stage', default='base,repeats,balanced')
    ap.add_argument('--record-reruns', action='store_true')
    ap.add_argument('--reproduce', type=int, metavar='N',
                    help='rerun N cached jobs (seeded draw, G < 400) from scratch and compare')
    a = ap.parse_args(argv)
    if a.record_reruns:
        return record_reruns()
    if a.reproduce:
        return reproduce(a.reproduce, a.jobs, tuple(a.stage.split(',')))
    js = [j for j in M.jobs(tuple(a.stage.split(','))) if j.variant is not None]
    res = {'date': NOW, 'harness_sha256': H.HARNESS_SHA256, 'dry_run': a.dry_run,
           'checked': CHECKED, 'designs': {}, 'jobs': {}, 'superseded': {}}
    with cf.ProcessPoolExecutor(a.jobs) as ex:
        dv = sorted({(j.variant, j.file) for j in js})
        for (v, f), st in zip(dv, ex.map(_design, [(v, f, a.dry_run) for v, f in dv])):
            res['designs'].setdefault(st, 0)
            res['designs'][st] += 1
            if st not in ('ok', 'restamp'):
                print('RTL %s %s: %s' % (v, pathlib.Path(f).name, st), flush=True)
        todo = [(j.variant, j.file, j.platform, j.flow, a.dry_run) for j in js]
        for i, (key, st, bad, nums) in enumerate(ex.map(_job, todo, chunksize=4)):
            v = key.split('|')[0]
            res['jobs'].setdefault(v, {}).setdefault(st, 0)
            res['jobs'][v][st] += 1
            if st == 'superseded':
                res['superseded'][key] = {'reasons': bad, 'before': nums}
                print('SUPERSEDED %s: %s' % (key, '; '.join(bad)[:300]), flush=True)
            if (i + 1) % 500 == 0:
                print('  %d/%d' % (i + 1, len(todo)), flush=True)
    print(json.dumps({'designs': res['designs'], 'jobs': res['jobs']}, indent=1))
    if not a.dry_run:
        out = HERE / 'results' / 'revalidation.json'
        prev = json.loads(out.read_text()) if out.exists() else {'runs': []}
        prev['runs'].append(res)
        out.write_text(json.dumps(prev, indent=1, sort_keys=True) + '\n')
    # status 1 while jobs need a rerun (superseded or missing): run.py, then --record-reruns
    return 1 if any(st in ('superseded', 'missing') for v in res['jobs'].values() for st in v) else 0


if __name__ == '__main__':
    sys.exit(main())
