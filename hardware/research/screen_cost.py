#!/usr/bin/env python3
"""What the screening procedure costs (-> results/screen_cost.json; summarised by timing.py).

    python3 hardware/research/screen_cost.py --n 60 --subset 20 --orders 5 -j 4   # runs the tools

The screening procedure is the part of a benchmark job that yields the synthesis-stage delay
(stages.synth.delay_ns of metrics.json), for one circuit, library and free flow:

  rtl       write rtl.v (verilog.rtl, or harness.shuffled_rtl(seed) for statement order seed > 0)
  yosys     hwbench.flow.synth unchanged: Yosys + ABC, mapped.v
  prep      parse mapped.v, simulate it through the Liberty functions (the exact switching
            activity that activity.tcl needs), write constraints.sdc and activity.tcl
  openroad  OpenROAD with flow.PNR_TCL, formatted as flow.pnr formats it and cut after the line
            ``hwb_report synth``, then ``exit``: read LEF/Liberty/mapped.v, link, read_sdc,
            activity, set_dont_use, buffer_ports -inputs, worst slack (OpenSTA), reports

The equivalence checks (RTL simulation and proof per circuit, the mapped netlist's proof per job)
are not in the timed path; with --checks they are timed separately afterwards.

The sample: candidates of sample.json + screen.json with G < 400, stratified by function
(n / 5 per function), drawn with a fixed seed; the order subset (subset / 5 per function) is
drawn first from the circuits that the synth1 and synth2 variant runs cover, so that orders 1 and
2 can be checked against those runs too.  Every job runs both libraries and both free flows.

Per step: wall time (perf_counter), CPU time of this process (process_time) and of its children
(getrusage(RUSAGE_CHILDREN) deltas; Yosys waits for ABC, so ABC is included), and the 1-minute
load average before and after.  Work folders: hardware/research/build/timing/ (not committed).
Startup: empty Yosys / OpenROAD runs and runs that only read the library (and LEFs), 5 each.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import contextlib
import json
import os
import pathlib
import random
import re
import resource
import shutil
import statistics as st
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import harness as H  # noqa: E402
from hwbench import design as D, flow as F, liberty as L, netlist as N, platforms as P, \
    verilog as V  # noqa: E402

REPO = HERE.parents[1]
TBUILD = H.RBUILD / 'timing'
OUT = HERE / 'results' / 'screen_cost.json'
SEED = 20261118
FREE = ('free', 'free-area')
STEPS = ('rtl', 'yosys', 'prep', 'openroad')


def pnr_kwargs(p):
    """The arguments flow.pnr formats PNR_TCL with (copied; the formatted prefix is compared
    with each reference job's pnr.tcl)."""
    return dict(tech_lef=p.path(p.tech_lef), sc_lef=p.path(p.sc_lef), lib=p.path(p.lib),
                util=F.UTILIZATION, space=F.CORE_SPACE_UM, site=p.site, platform=p.dir,
                io_h=p.io_h, io_v=p.io_v, density=min(0.95, F.UTILIZATION / 100 + 0.2),
                min_route=p.min_route, max_route=p.max_route, gr_adjust=F.GR_ADJUST[p.name],
                dont_use=' '.join(p.dont_use),
                port_buffer_dont_use=F.PORT_BUFFER_DONT_USE.get(p.name, ''))


CUT = '\nhwb_report synth\n'


def screen_prefix(p):
    full = H._PNR.format(**pnr_kwargs(p))
    assert full.count(CUT) == 1
    return full[:full.index(CUT) + len(CUT)]


def screen_tcl(p):
    return screen_prefix(p) + 'exit\n'


class Meter:
    def __init__(self):
        self.steps = {}

    @contextlib.contextmanager
    def __call__(self, name):
        r0 = resource.getrusage(resource.RUSAGE_CHILDREN)
        w0, c0 = time.perf_counter(), time.process_time()
        yield
        w1, c1 = time.perf_counter(), time.process_time()
        r1 = resource.getrusage(resource.RUSAGE_CHILDREN)
        ch = (r1.ru_utime + r1.ru_stime) - (r0.ru_utime + r0.ru_stime)
        self.steps[name] = {'wall': round(w1 - w0, 4), 'cpu_self': round(c1 - c0, 4),
                            'cpu_children': round(ch, 4), 'cpu': round(c1 - c0 + ch, 4)}


_LIBS = {}


def _init():
    for pl in P.PLATFORMS:
        p = P.get(pl)
        _LIBS[pl] = L.load(p.path(p.lib), cache_dir=TBUILD / '_liberty')


def reference(d, plat, flow, order):
    variant = 'base' if order == 0 else 'synth%d' % order
    f = H.RBUILD / variant / d.id / plat / flow
    return f if (f / 'metrics.json').exists() else None


def _job(args):
    file, plat, flow, order, checks = args
    d = D.load(file)
    p = P.get(plat)
    lib = _LIBS[plat]
    # a folder per job (design_dir is per job too), so that parallel jobs never share rtl.v
    F.BUILD = TBUILD / ('o%d' % order) / plat / flow
    ddir = F.design_dir(d)
    out = F.job_dir(d, plat, flow)
    if ddir.exists():
        shutil.rmtree(ddir)
    out.mkdir(parents=True)
    rec = {'file': str(pathlib.Path(file).relative_to(REPO).as_posix()), 'design': d.id,
           'function': d.function, 'G': d.metrics['G'], 'A': d.metrics.get('A', 0),
           'platform': plat, 'flow': flow, 'order': order, 'load_before': os.getloadavg()[0]}
    m = Meter()
    with m('rtl'):
        (ddir / 'rtl.v').write_text((V.rtl if order == 0 else H.shuffled_rtl(order))(d))
    with m('yosys'):
        F.synth(d, p, flow, out, lib)
    with m('prep'):
        nl = N.parse((out / 'mapped.v').read_text())
        sim = N.simulate(nl, lib, d, V.vectors(d), p.physical)
        if sim.mismatches:
            raise F.CheckFailed('%s: mapped netlist differs: %s' % (d.id, sim.first_mismatch))
        (out / 'constraints.sdc').write_text(F.sdc(p, lib))
        (out / 'activity.tcl').write_text(F.activity_tcl(nl, lib, sim, p.physical))
        (out / 'screen.tcl').write_text(screen_tcl(p))
    with m('openroad'):
        log = F.tool('openroad', ['openroad', '-no_init', '-no_splash', '-exit', 'screen.tcl'],
                     out, out / 'screen.log')
    rec['load_after'] = os.getloadavg()[0]
    rec['steps'] = m.steps
    rec['total'] = {k: round(sum(s[k] for s in m.steps.values()), 4) for k in ('wall', 'cpu')}
    slack = float(re.search(r'^HWB synth worst_slack (\S+)', log, re.M).group(1))
    rec['delay_ns'] = round(F.PERIOD_NS - slack, 6)
    ref = reference(d, plat, flow, order)
    if ref:
        r = json.loads((ref / 'metrics.json').read_text())
        rec['ref'] = ref.relative_to(REPO).as_posix()
        rec['ref_delay_ns'] = r['stages']['synth']['delay_ns']
        rec['ref_cells'] = r['cell_types']
        rec['cells_match'] = sim.cells == r['cell_types']
        rec['tcl_prefix_match'] = (ref / 'pnr.tcl').read_text().startswith(screen_prefix(p))
    if checks and order == 0:
        cm = Meter()
        (ddir / 'spec.v').write_text(V.spec(d))
        with cm('check_mapped'):
            F.formal_equiv(out, 'mapped.v', out / 'mapped_cec.log', liberty=p.path(p.lib))
        with cm('check_rtl'):          # per circuit; F.prepare overwrites rtl.v with itself
            F.prepare(d)
        rec['checks'] = cm.steps
    return rec


def _calibrate(reps=5):
    """Process startup: empty runs, and runs that only read the library (and LEFs)."""
    cdir = TBUILD / 'startup'
    cdir.mkdir(parents=True, exist_ok=True)
    out = []
    for pl in P.PLATFORMS:
        p = P.get(pl)
        kw = pnr_kwargs(p)
        cases = {
            'yosys_empty': ('yosys', ['yosys', '-s', 'empty.ys'], 'empty.ys', ''),
            'yosys_read_liberty': ('yosys', ['yosys', '-s', 'lib.ys'], 'lib.ys',
                                   'read_liberty -lib %s\n' % kw['lib']),
            'openroad_empty': ('openroad', ['openroad', '-no_init', '-no_splash', '-exit',
                                            'empty.tcl'], 'empty.tcl', 'exit\n'),
            'openroad_read_lef_liberty': ('openroad', ['openroad', '-no_init', '-no_splash',
                                                       '-exit', 'lib.tcl'], 'lib.tcl',
                                          'read_lef %s\nread_lef %s\nread_liberty %s\nexit\n'
                                          % (kw['tech_lef'], kw['sc_lef'], kw['lib'])),
        }
        for name, (env, args, fn, text) in cases.items():
            (cdir / fn).write_text(text)
            for _ in range(reps):
                m = Meter()
                with m(name):
                    F.tool(env, args, cdir, cdir / (fn + '.log'))
                out.append(dict(m.steps[name], platform=pl, case=name,
                                load=os.getloadavg()[0]))
    return out


def sample(n, subset, seed=SEED):
    """n circuits with G < 400 (n / 5 per function); the first subset of them (subset / 5 per
    function, from those the synth1/synth2 runs cover where possible) get every order."""
    seen, cands = set(), []
    for name in ('sample.json', 'screen.json'):
        for e in json.loads((HERE / name).read_text())['candidates']:
            if e['G'] < 400 and e['file'] not in seen:
                seen.add(e['file'])
                cands.append(e)
    by = {}
    for e in sorted(cands, key=lambda e: e['file']):
        by.setdefault(e['function'], []).append(e)
    rng = random.Random(seed)
    k, ks = n // len(by), subset // len(by)
    sub, rest = [], []
    for fn in sorted(by):
        ok, seeded = [], []
        for e in by[fn]:
            d = D.load(str(REPO / e['file']))
            if all(reference(d, pl, fl, 0) for pl in P.PLATFORMS for fl in FREE):
                ok.append(e)
                if all(reference(d, pl, fl, s) for pl in P.PLATFORMS for fl in FREE
                       for s in (1, 2)):
                    seeded.append(e)
        a = rng.sample(seeded, min(ks, len(seeded)))
        a += rng.sample([e for e in ok if e not in a], ks - len(a))
        b = rng.sample([e for e in ok if e not in a], k - ks)
        sub += a
        rest += b
    return [str(REPO / e['file']) for e in sub], [str(REPO / e['file']) for e in rest]


def measure(n=60, subset=20, orders=5, jobs=4, checks=True, seed=SEED, out=OUT):
    t0 = time.time()
    sub, rest = sample(n, subset, seed)
    if TBUILD.exists():
        shutil.rmtree(TBUILD)
    TBUILD.mkdir(parents=True)
    _init()
    load0 = os.getloadavg()
    cal = _calibrate()
    tasks = [(f, pl, fl, o, checks) for f in sub + rest for o in range(orders if f in sub else 1)
             for pl in P.PLATFORMS for fl in FREE]
    print('screen cost: %d circuits (%d with %d orders), %d jobs, -j %d'
          % (len(sub) + len(rest), len(sub), orders, len(tasks), jobs), flush=True)
    recs, fails = [], []
    with cf.ProcessPoolExecutor(jobs, initializer=_init) as ex:
        futs = {ex.submit(_job, t): t for t in tasks}
        for i, fu in enumerate(cf.as_completed(futs)):
            try:
                recs.append(fu.result())
            except Exception as e:
                t = futs[fu]
                fails.append({'file': t[0], 'platform': t[1], 'flow': t[2], 'order': t[3],
                              'error': '%s: %s' % (type(e).__name__, str(e)[:300])})
            if (i + 1) % 50 == 0:
                print('  %d/%d, %.0f s, load %.1f' % (i + 1, len(tasks), time.time() - t0,
                                                     os.getloadavg()[0]), flush=True)
    recs.sort(key=lambda r: (r['file'], r['platform'], r['flow'], r['order']))
    data = {'meta': {'seed': seed, 'n': len(sub) + len(rest), 'subset': len(sub),
                     'orders': orders, 'jobs': jobs, 'checks': checks,
                     'subset_files': sorted(str(pathlib.Path(f).relative_to(REPO).as_posix())
                                            for f in sub),
                     'cpu_count': os.cpu_count(), 'loadavg_start': load0,
                     'loadavg_end': os.getloadavg(), 'seconds': round(time.time() - t0, 1),
                     'date': time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(t0)),
                     'tools': F.versions(),
                     'command': 'python3 hardware/research/timing.py --measure-screen %d '
                                '--subset %d --orders %d -j %d%s'
                                % (n, subset, orders, jobs, '' if checks else ' --no-checks')},
            'startup': cal, 'failures': fails, 'records': recs}
    out.write_text(json.dumps(data, indent=0) + '\n')
    return data


# ---- summary ------------------------------------------------------------------------------

def q(v, x):
    return sorted(v)[int(x * (len(v) - 1))]


def dist(v, nd=3):
    return {'n': len(v), 'median': round(st.median(v), nd), 'p10': round(q(v, .1), nd),
            'p90': round(q(v, .9), nd)}


def wc(rs, get=lambda r, k: r['total'][k]):
    return {k: dist([get(r, k) for r in rs]) for k in ('wall', 'cpu')}


def summarize(data):
    recs = data['records']
    meta = data['meta']
    sub = set(meta['subset_files'])
    one = [r for r in recs if r['order'] == 0]
    cfgs = sorted({(r['platform'], r['flow']) for r in recs})
    screen = {
        'definition': 'Yosys + ABC (flow.synth) then OpenROAD/OpenSTA up to hwb_report synth '
                      '(flow.PNR_TCL cut there): the stages.synth delay, one statement order, '
                      'per circuit-library-flow; equivalence checks not included',
        'n_circuits': len({r['file'] for r in one}), 'n': len(one),
        'all': wc(one),
        'by_config': {'%s/%s' % c: wc([r for r in one if (r['platform'], r['flow']) == c])
                      for c in cfgs},
        'steps': {s: wc(one, lambda r, k, s=s: r['steps'][s][k]) for s in STEPS},
        'per_circuit_2_libraries_2_flows': wc(
            [{'total': {k: sum(r['total'][k] for r in one if r['file'] == f) for k in
                        ('wall', 'cpu')}} for f in sorted({r['file'] for r in one})]),
        'loadavg_1min': dist([r['load_before'] for r in one], 1),
        'jobs_in_parallel': meta['jobs'], 'cpu_count': meta['cpu_count'],
    }
    # k orders: the sum over orders 0..k-1 for each circuit-library-flow of the subset
    sr = [r for r in recs if r['file'] in sub]
    keyed = {}
    for r in sr:
        keyed.setdefault((r['file'], r['platform'], r['flow']), {})[r['order']] = r
    orders = {'subset_circuits': len(sub), 'measured_orders': meta['orders'],
              'note': 'every k up to measured_orders is measured (orders 0..k-1, 0 = the '
                      'benchmark\'s RTL), none extrapolated; values per circuit-library-flow'}
    for k in (1, 3, 5):
        if k > meta['orders']:
            orders['k%d' % k] = 'not measured'
            continue
        tot = [{'total': {m: sum(g[o]['total'][m] for o in range(k)) for m in ('wall', 'cpu')}}
               for g in keyed.values() if all(o in g for o in range(k))]
        circ = {}
        for (f, _, _), g in keyed.items():
            if all(o in g for o in range(k)):
                c = circ.setdefault(f, {'wall': 0.0, 'cpu': 0.0})
                for m in c:
                    c[m] += sum(g[o]['total'][m] for o in range(k))
        orders['k%d' % k] = dict(wc(tot), per_circuit_2_libraries_2_flows=wc(
            [{'total': c} for c in circ.values()]))
    # verification against the benchmark runs
    cmp_ = [r for r in recs if 'ref_delay_ns' in r]
    mism = [{'design': r['design'], 'platform': r['platform'], 'flow': r['flow'],
             'order': r['order'], 'delay_ns': r['delay_ns'], 'ref_delay_ns': r['ref_delay_ns'],
             'cells_match': r['cells_match']}
            for r in cmp_ if r['delay_ns'] != r['ref_delay_ns']]
    verify = {'compared': len(cmp_), 'exact': len(cmp_) - len(mism),
              'by_order': {o: sum(1 for r in cmp_ if r['order'] == o)
                           for o in sorted({r['order'] for r in cmp_})},
              'cells_identical': sum(1 for r in cmp_ if r['cells_match']),
              'tcl_prefix_identical': sum(1 for r in cmp_ if r['tcl_prefix_match']),
              'reference': 'stages.synth.delay_ns of build/base (order 0) and build/synth1, '
                           'synth2 (orders 1, 2) metrics.json',
              'mismatches': mism, 'failures': data['failures']}
    startup = {}
    for c in sorted({(s['platform'], s['case']) for s in data['startup']}):
        v = [s for s in data['startup'] if (s['platform'], s['case']) == c]
        startup['%s/%s' % c] = {k: round(st.median([s[k] for s in v]), 3) for k in ('wall', 'cpu')}
    out = {'screen_synth_sta_s': screen, 'screen_orders_s': orders, 'screen_verify': verify,
           'startup_s': startup}
    ch = [r for r in one if 'checks' in r]
    if ch:
        out['checks_s'] = {
            'note': 'not in the screening path; check_mapped per job (ABC &cec of mapped.v), '
                    'check_rtl per circuit (Icarus simulation + proof of rtl.v)',
            'check_mapped': wc(ch, lambda r, k: r['checks']['check_mapped'][k]),
            'check_rtl': wc(ch, lambda r, k: r['checks']['check_rtl'][k])}
    out['screen_measurement'] = {k: meta[k] for k in ('date', 'seed', 'n', 'subset', 'orders',
                                                      'jobs', 'cpu_count', 'loadavg_start',
                                                      'loadavg_end', 'seconds', 'command')}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, default=60)
    ap.add_argument('--subset', type=int, default=20)
    ap.add_argument('--orders', type=int, default=5)
    ap.add_argument('-j', '--jobs', type=int, default=4)
    ap.add_argument('--no-checks', action='store_true')
    a = ap.parse_args(argv)
    data = measure(a.n, a.subset, a.orders, a.jobs, not a.no_checks)
    print(json.dumps(summarize(data), indent=1))


if __name__ == '__main__':
    main()
