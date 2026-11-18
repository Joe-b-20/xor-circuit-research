#!/usr/bin/env python3
"""The study's expected jobs, and the check that the results on disk are exactly those.

    python3 hardware/research/manifest.py                     # check every stage
    python3 hardware/research/manifest.py --stage baseline,base
    python3 hardware/research/manifest.py --list repeats      # print a stage's jobs

Stages (in run order):
  baseline  the benchmark's 340 circuits x 2 libraries x 3 flows (2,040 jobs) in hardware/build/,
            run by ``hardware/bench.py run --suite all``; benchmark fingerprints
  base      the candidates (lists/candidates-small.txt, lists/screen.txt: every library and flow;
            lists/candidates-large.txt, G >= 400: Nangate45 and SKY130 preserve only) in
            build/base/
  repeats   placement seeds pnr1-3 on every flow and statement-order seeds synth1-2 on the free
            flows, for lists/seeds-small.txt (and lists/seeds-large.txt with the large rule)
  balanced  lists/balanced.txt: orders x placements on chosen circuits (o<O>p<P> variants)
plus lists/extra.txt: single jobs outside these rules that are part of the results.

A job is *ok* when its metrics.json exists (it exists only when every check passed) and its
fingerprint is the one the current code, tools, circuit, library and (research jobs) harness and
variant settings give.  Otherwise it is *missing* or *stale*.  Results on disk that the manifest
does not list are reported and never collected.  Exit status 1 when a job is missing or stale.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import harness as H  # noqa: E402
import bench  # noqa: E402
from hwbench import design as D, flow as F, platforms as P  # noqa: E402

REPO = HERE.parents[1]
LISTS = HERE / 'lists'
BENCH_BUILD = HERE.parent / 'build'
STAGES = ('baseline', 'base', 'repeats', 'balanced')
ALL = [(p, f) for p in P.PLATFORMS for f in F.FLOWS]
LARGE = [('nangate45', f) for f in F.FLOWS] + [('sky130hd', 'preserve')]
FREE = ('free', 'free-area')


class Job(collections.namedtuple('Job', 'stage variant file platform flow why')):
    """variant None: a benchmark job (hardware/build); else the research variant's folder name."""

    def design(self):
        return D.load(self.file)

    def build(self):
        return BENCH_BUILD if self.variant is None else H.RBUILD / self.variant

    def key(self):
        return (self.variant, pathlib.Path(self.file).name, self.platform, self.flow)


def read_list(name):
    out = []
    for line in (LISTS / name).read_text().splitlines():
        f = line.split('#')[0].strip()
        if f:
            out.append(str(REPO / f))
    return out


def read_jobs_file(name):
    """Lines 'stage variant(s) platform(s) flow(s) file  # why'; commas give every combination."""
    out = []
    f = LISTS / name
    if not f.exists():
        return out
    for line in f.read_text().splitlines():
        body, _, why = line.partition('#')
        parts = body.split()
        if not parts:
            continue
        if len(parts) != 5:
            raise SystemExit('%s: bad line %r' % (f, line))
        stage, vs, ps, fs, path = parts
        if stage not in STAGES[1:]:
            raise SystemExit('%s: unknown stage %s' % (f, stage))
        if name == 'balanced.txt' and stage != 'balanced':
            raise SystemExit('%s: stage %s in the balanced list' % (f, stage))
        for v in vs.split(','):
            for p in ps.split(','):
                for fl in fs.split(','):
                    if p not in P.PLATFORMS or fl not in F.FLOWS:
                        raise SystemExit('%s: bad platform/flow in %r' % (f, line))
                    out.append(Job(stage, H.canonical(v), str(REPO / path), p, fl, why.strip()))
    return out


def jobs(stages=STAGES):
    out = []
    if 'baseline' in stages:
        for f in bench.expand(bench.suite('all')):
            out += [Job('baseline', None, str(f), p, fl, 'benchmark') for p, fl in ALL]
    if 'base' in stages:
        for f in read_list('candidates-small.txt') + read_list('screen.txt'):
            out += [Job('base', 'base', f, p, fl, 'candidate') for p, fl in ALL]
        for f in read_list('candidates-large.txt'):
            out += [Job('base', 'base', f, p, fl, 'candidate, G >= 400') for p, fl in LARGE]
    if 'repeats' in stages:
        small, large = read_list('seeds-small.txt'), read_list('seeds-large.txt')
        for s in (1, 2, 3):
            v = 'pnr%d' % s
            out += [Job('repeats', v, f, p, fl, 'seeds.txt') for f in small for p, fl in ALL]
            out += [Job('repeats', v, f, p, fl, 'seeds.txt') for f in large for p, fl in LARGE]
        for s in (1, 2):
            v = 'synth%d' % s
            out += [Job('repeats', v, f, p, fl, 'seeds.txt') for f in small for p, fl in ALL
                    if fl in FREE]
            out += [Job('repeats', v, f, p, fl, 'seeds.txt') for f in large for p, fl in LARGE
                    if fl in FREE]
    out += [j for j in read_jobs_file('extra.txt') if j.stage in stages]
    if 'balanced' in stages:
        out += [j for j in read_jobs_file('balanced.txt') if j.stage == 'balanced']
    seen, uniq = set(), []
    for j in out:
        if j.key() not in seen:
            seen.add(j.key())
            uniq.append(j)
    return uniq


def expected_fingerprint(job, d=None):
    d = d or job.design()
    parts = (d.sha256, job.platform, job.flow, H.lib_sha(job.platform))
    return H.bench_fingerprint(*parts) if job.variant is None else H.job_fingerprint(job.variant, *parts)


def metrics_file(job, d=None):
    d = d or job.design()
    return job.build() / d.id / job.platform / job.flow / 'metrics.json'


def check(stages=STAGES, js=None):
    """{'ok': [(job, metrics)], 'missing': [job], 'stale': [(job, reason)], 'unlisted': [path]}."""
    js = jobs(stages) if js is None else js
    res = {'ok': [], 'missing': [], 'stale': [], 'unlisted': []}
    designs = {}
    listed = set()
    for j in js:
        d = designs.get(j.file) or designs.setdefault(j.file, j.design())
        mf = metrics_file(j, d)
        listed.add(mf)
        if not mf.exists():
            res['missing'].append(j)
            continue
        r = json.loads(mf.read_text())
        want = expected_fingerprint(j, d)
        if r.get('fingerprint') != want:
            res['stale'].append((j, 'fingerprint %s, expected %s' % (r.get('fingerprint'), want)))
            continue
        if r.get('design') != d.id or r.get('platform') != j.platform or r.get('flow') != j.flow:
            res['stale'].append((j, 'metrics.json describes another job'))
            continue
        if j.variant is not None and (r.get('research') or {}).get('settings') != H.settings(j.variant):
            res['stale'].append((j, 'no or different research settings record'))
            continue
        res['ok'].append((j, r))
    builds = {j.build() for j in js}
    for b in builds:
        for mf in b.glob('*/*/*/metrics.json'):
            if mf not in listed:
                res["unlisted"].append(str(mf))
    return res


def summary(res):
    by = collections.Counter()
    for k in ('ok', 'missing', 'stale'):
        for x in res[k]:
            j = x if isinstance(x, Job) else x[0]
            by[(j.stage, j.variant or 'benchmark', k)] += 1
    lines = []
    for st in STAGES:
        vs = sorted({v for (s, v, _) in by if s == st})
        for v in vs:
            lines.append('%-9s %-9s ok %5d  missing %4d  stale %4d' % (
                st, v, by[(st, v, 'ok')], by[(st, v, 'missing')], by[(st, v, 'stale')]))
    lines.append('results on disk outside the manifest (not collected): %d' % len(res['unlisted']))
    return '\n'.join(lines)


def require(stages=STAGES, js=None, out=None):
    """check() and raise SystemExit(1) when a job is missing or stale."""
    out = out or sys.stdout
    res = check(stages, js)
    print(summary(res), file=out)
    bad = len(res['missing']) + len(res['stale'])
    if bad:
        for j in res['missing'][:20]:
            print('MISSING', j.stage, j.variant or 'benchmark', pathlib.Path(j.file).name,
                  j.platform, j.flow, file=out)
        for j, why in res['stale'][:20]:
            print('STALE  ', j.stage, j.variant or 'benchmark', pathlib.Path(j.file).name,
                  j.platform, j.flow, why, file=out)
        raise SystemExit('%d jobs missing or stale (stages %s): nothing collected'
                         % (bad, ','.join(stages)))
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', default=','.join(STAGES), help='comma-separated stages')
    ap.add_argument('--list', metavar='STAGE', help='print the jobs of a stage and exit')
    a = ap.parse_args(argv)
    if a.list:
        for j in jobs((a.list,)):
            print(j.stage, j.variant or 'benchmark', j.platform, j.flow,
                  pathlib.Path(j.file).relative_to(REPO).as_posix(), '#', j.why)
        return 0
    stages = tuple(a.stage.split(','))
    for s in stages:
        if s not in STAGES:
            raise SystemExit('unknown stage %s' % s)
    require(stages)
    return 0


if __name__ == '__main__':
    sys.exit(main())
