#!/usr/bin/env python3
"""Run benchmark jobs for the research study (isolated build folder, optional noise seeds).

    python3 hardware/research/run.py --stage base -j 19        # a stage of manifest.py
    python3 hardware/research/run.py --list LIST --variant pnr3 [-p nangate45] [-f preserve]
    python3 hardware/research/run.py --list LIST --variant o2p1      # statement order 2, placement 1

Variants: harness.py.  Results: hardware/research/build/<variant>/<circuit>/<library>/<flow>/
metrics.json, the benchmark's files plus the research record; a job whose fingerprint matches is
not rerun.  Failures (with the reason) go to build/<variant>/failures.jsonl, and the exit status
is 1 when any circuit's preparation or any job failed.  The benchmark's own 340 circuits run with
``hardware/bench.py run --suite all``.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import pathlib
import sys
import time
import traceback

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import harness as H  # noqa: E402
import manifest as M  # noqa: E402
import bench  # noqa: E402
from hwbench import flow as F, platforms as P  # noqa: E402

REPO = HERE.parents[1]


def _prepare(args):
    variant, path = args
    try:
        H.prepare_design(path, variant)
        return None
    except Exception as e:
        return '%s: %s' % (type(e).__name__, e)


def _job(args):
    variant, path, plat, flow = args
    try:
        r = H.run_job(path, plat, flow, variant)
        return ('ok', variant, path, plat, flow, r['seconds'])
    except Exception as e:
        return ('fail', variant, path, plat, flow, '%s: %s | %s' % (
            type(e).__name__, str(e)[:300], traceback.format_exc(limit=2)[-300:]))


def run(todo, jobs):
    """Run (variant, file, platform, flow) jobs; returns the list of failures."""
    t0 = time.time()
    fails = []
    preps = sorted({(v, f) for v, f, _, _ in todo})
    mapper = (lambda fn, xs: map(fn, xs)) if jobs == 1 else None
    ex = None if jobs == 1 else cf.ProcessPoolExecutor(jobs)
    try:
        m = mapper or (lambda fn, xs: ex.map(fn, xs, chunksize=1))
        for (v, f), err in zip(preps, m(_prepare, preps)):
            if err:
                fails.append({'variant': v, 'file': f, 'stage': 'prepare', 'error': err})
                print('FAIL prepare %s %s: %s' % (v, pathlib.Path(f).name, err[:200]), flush=True)
        bad = {(x['variant'], x['file']) for x in fails}
        todo = [t for t in todo if (t[0], t[1]) not in bad]
        print('%d circuits, %d jobs' % (len({f for _, f, _, _ in todo}), len(todo)), flush=True)
        for i, (st, v, f, p, fl, info) in enumerate(m(_job, todo)):
            if st != 'ok':
                fails.append({'variant': v, 'file': f, 'platform': p, 'flow': fl, 'error': info})
                print('FAIL %s %s %s %s: %s' % (v, pathlib.Path(f).name, p, fl, info[:200]),
                      flush=True)
            if (i + 1) % 200 == 0:
                print('  %d/%d jobs, %.0f s' % (i + 1, len(todo), time.time() - t0), flush=True)
    finally:
        if ex:
            ex.shutdown()
    for v in sorted({t[0] for t in todo} | {x['variant'] for x in fails}):
        d = H.RBUILD / v
        d.mkdir(parents=True, exist_ok=True)
        with open(d / 'failures.jsonl', 'w') as fh:
            for x in fails:
                if x['variant'] == v:
                    fh.write(json.dumps(x) + '\n')
    print('done: %d jobs, %d failures, %.0f s' % (len(todo), len(fails), time.time() - t0))
    return fails


def main(argv=None):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--stage', help='a research stage of manifest.py: base, repeats or balanced')
    g.add_argument('--list', help='a list of circuit files (with --variant, -p, -f)')
    ap.add_argument('--variant', default='base')
    ap.add_argument('-p', '--platforms', type=lambda s: s.split(','), default=list(P.PLATFORMS))
    ap.add_argument('-f', '--flows', type=lambda s: s.split(','), default=list(F.FLOWS))
    ap.add_argument('-j', '--jobs', type=int, default=os.cpu_count())
    a = ap.parse_args(argv)
    if a.stage:
        if a.stage not in M.STAGES[1:]:
            raise SystemExit('stage %s: one of %s (the baseline runs with hardware/bench.py)'
                             % (a.stage, ', '.join(M.STAGES[1:])))
        todo = [(j.variant, j.file, j.platform, j.flow) for j in M.jobs((a.stage,))]
    else:
        v = H.canonical(a.variant)
        files = [str(REPO / l.split('#')[0].strip()) for l in open(a.list)
                 if l.split('#')[0].strip()]
        todo = [(v, f, p, fl) for f in files for p in a.platforms for fl in a.flows]
    if os.environ.get("HWRESEARCH_CHECK_LIBRARIES", "1") != "0":   # 0: tests only
        bench.check_libraries()      # the pinned Liberty files (tools/platforms.sha256)
    fails = run(todo, a.jobs)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
