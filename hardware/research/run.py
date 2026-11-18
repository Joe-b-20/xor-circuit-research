#!/usr/bin/env python3
"""Run benchmark jobs for the research study (isolated build folder, optional noise seeds).

    python3 hardware/research/run.py --list hardware/research/lists/candidates-small.txt --variant base -j 19
    python3 hardware/research/run.py --list LIST --variant pnr3      # placement/routing seed 3
    python3 hardware/research/run.py --list LIST --variant synth3    # + RTL statement order seed 3

Results: hardware/research/build/<variant>/<circuit>/<library>/<flow>/metrics.json, the same
files as the benchmark's; failures (with the reason) in hardware/research/build/<variant>/failures.jsonl.
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
from hwbench import design as D, flow as F, platforms as P  # noqa: E402

REPO = HERE.parents[1]


def _init(variant):
    H.set_variant(variant)


def _prepare(path):
    try:
        F.prepare_design(path)
        return None
    except Exception as e:
        return '%s: %s' % (type(e).__name__, e)


def _job(args):
    path, plat, flow = args
    try:
        r = F.run_job(path, plat, flow)
        return ('ok', path, plat, flow, r['seconds'])
    except Exception as e:
        return ('fail', path, plat, flow, '%s: %s | %s' % (type(e).__name__, str(e)[:300],
                                                           traceback.format_exc(limit=2)[-300:]))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--list', required=True)
    ap.add_argument('--variant', default='base')
    ap.add_argument('-p', '--platforms', type=lambda s: s.split(','), default=list(P.PLATFORMS))
    ap.add_argument('-f', '--flows', type=lambda s: s.split(','), default=list(F.FLOWS))
    ap.add_argument('-j', '--jobs', type=int, default=os.cpu_count())
    a = ap.parse_args(argv)
    H.set_variant(a.variant)
    files = [str(REPO / l.split('#')[0].strip()) for l in open(a.list) if l.split('#')[0].strip()]
    out = F.BUILD
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    fails = []
    with cf.ProcessPoolExecutor(a.jobs, initializer=_init, initargs=(a.variant,)) as ex:
        for f, err in zip(files, ex.map(_prepare, files)):
            if err:
                fails.append({'file': f, 'stage': 'prepare', 'error': err})
        bad = {x['file'] for x in fails}
        todo = [(f, p, fl) for f in files if f not in bad for p in a.platforms for fl in a.flows]
        print('%s: %d circuits, %d jobs' % (a.variant, len(files), len(todo)), flush=True)
        for i, (st, f, p, fl, info) in enumerate(ex.map(_job, todo, chunksize=1)):
            if st != 'ok':
                fails.append({'file': f, 'platform': p, 'flow': fl, 'error': info})
                print('FAIL %s %s %s: %s' % (pathlib.Path(f).name, p, fl, info[:200]), flush=True)
            if (i + 1) % 200 == 0:
                print('  %d/%d jobs, %.0f s' % (i + 1, len(todo), time.time() - t0), flush=True)
    with open(out / 'failures.jsonl', 'w') as fh:
        for x in fails:
            fh.write(json.dumps(x) + '\n')
    print('%s done: %d jobs, %d failures, %.0f s' % (a.variant, len(todo), len(fails), time.time() - t0))


if __name__ == '__main__':
    main()
