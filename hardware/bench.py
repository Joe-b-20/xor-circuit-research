#!/usr/bin/env python3
"""Hardware benchmark of XORFlux/BoolFlux circuits against NIST's: run, pair, tabulate.

    python3 hardware/bench.py run --suite first-pair            # the first pair, both libraries
    python3 hardware/bench.py run --suite all -j 16             # every circuit of the suites
    python3 hardware/bench.py run FILE_OR_DIR ... [-p nangate45] [-f preserve]
    python3 hardware/bench.py table                             # results/ from the build folder
    python3 hardware/bench.py pairs                             # print the pairing

Tools: hardware/tools/install.sh.  Build folder: hardware/build/ (HWBENCH_BUILD to move it).
Every job checks equivalence (simulation and SAT) at RTL, mapped and routed stages and stops
with an error if a check fails; see hwbench/flow.py.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import pathlib
import sys
import traceback

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from hwbench import design as D, flow as F, pairs as PR, platforms as P, report as R  # noqa: E402

SUITES = HERE / 'suites'


def expand(items):
    files = []
    for it in items:
        p = pathlib.Path(it)
        if not p.is_absolute():
            p = (D.REPO / it) if (D.REPO / it).exists() else p.resolve()
        if p.is_dir():
            files += sorted(p.glob('*.circ.txt'))
        elif p.exists():
            files.append(p)
        else:
            raise SystemExit('no such circuit file or folder: %s' % it)
    return files


def suite(name):
    f = SUITES / ('%s.txt' % name)
    if not f.exists():
        raise SystemExit('no suite %s (suites: %s)' % (
            name, ', '.join(sorted(s.stem for s in SUITES.glob('*.txt')))))
    items = []
    for line in f.read_text().splitlines():
        line = line.split('#')[0].strip()
        if line.startswith('@'):
            items += suite(line[1:])
        elif line:
            items.append(line)
    return items


def check_libraries():
    """Refuse to run on Liberty files other than the pinned ones (tools/platforms.sha256)."""
    for line in (HERE / 'tools' / 'platforms.sha256').read_text().splitlines():
        digest, rel = line.split()
        f = P.ORFS / rel
        if not f.exists() or hashlib.sha256(f.read_bytes()).hexdigest() != digest:
            raise SystemExit('%s differs from the pinned file (tools/platforms.sha256)' % f)


def _prepare(args):
    path, force = args
    d, _ = F.prepare_design(path, force=force)
    return d.id


def _job(args):
    path, platform, flow, force = args
    try:
        r = F.run_job(path, platform, flow, force=force)
        return ('ok', path, platform, flow, r['seconds'])
    except Exception as e:      # reported, and the run exits non-zero
        return ('fail', path, platform, flow, '%s: %s\n%s' % (type(e).__name__, e,
                                                               traceback.format_exc(limit=3)))


def cmd_run(a):
    items = list(a.paths)
    for s in a.suite or []:
        items += suite(s)
    files = expand(items)
    if not files:
        raise SystemExit('nothing to run')
    for p in a.platforms:
        if not P.get(p).path(P.get(p).lib).exists():
            raise SystemExit('platform %s is not installed (hardware/tools/install.sh)' % p)
    check_libraries()
    jobs = os.cpu_count() if a.jobs <= 0 else a.jobs
    print('%d circuits x %d platforms x %d flows, %d parallel jobs'
          % (len(files), len(a.platforms), len(a.flows), jobs), flush=True)
    failures = []
    with cf.ProcessPoolExecutor(jobs) as ex:
        list(ex.map(_prepare, [(f, a.force) for f in files]))   # Verilog, RTL checks: once each
        todo = [(f, p, fl, a.force) for f in files for p in a.platforms for fl in a.flows]
        done = 0
        for st, path, p, fl, info in ex.map(_job, todo):
            done += 1
            if st == 'ok':
                if a.verbose:
                    print('ok   %s %s %s (%ss)' % (path.name, p, fl, info), flush=True)
            else:
                failures.append((path, p, fl, info))
                print('FAIL %s %s %s\n%s' % (path.name, p, fl, info), flush=True)
            if done % 50 == 0:
                print('  %d/%d jobs' % (done, len(todo)), flush=True)
    print('%d jobs, %d failed' % (len(todo), len(failures)))
    return 1 if failures else 0


def cmd_pairs(a):
    designs = [D.load(f) for f in expand(suite('all'))]
    ours = [d for d in designs if d.origin == 'ours']
    nist = [d for d in designs if d.origin == 'nist']
    for n, o in PR.pair(ours, nist):
        print('%-12s NIST %-14s ours %s' % (n.function, n.label, o.label if o else '-'))
    return 0


def cmd_table(a):
    R.write(F.BUILD, HERE / 'results', [D.load(f) for f in expand(suite('all'))])
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('run')
    r.add_argument('paths', nargs='*')
    r.add_argument('--suite', action='append')
    r.add_argument('-p', '--platforms', type=lambda s: s.split(','), default=list(P.PLATFORMS))
    r.add_argument('-f', '--flows', type=lambda s: s.split(','), default=list(F.FLOWS))
    r.add_argument('-j', '--jobs', type=int, default=0)
    r.add_argument('--force', action='store_true', help='rerun jobs that have results')
    r.add_argument('-v', '--verbose', action='store_true')
    sub.add_parser('pairs')
    sub.add_parser('table')
    a = ap.parse_args(argv)
    return {'run': cmd_run, 'pairs': cmd_pairs, 'table': cmd_table}[a.cmd](a)


if __name__ == '__main__':
    sys.exit(main())
