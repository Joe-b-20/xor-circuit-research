#!/usr/bin/env python3
"""What the scores and the screening cost (-> results/timing.json).

    python3 hardware/research/timing.py                        # summarise (no tools run)
    python3 hardware/research/timing.py --measure-screen 60    # first re-measure the screening
                                                               # (runs Yosys/OpenROAD, ~10 min)

  features_s          wall time of features.features() per circuit (all three scores, both
                      libraries), over every candidate and baseline circuit, on one core
  synthesis_only_s    Yosys + ABC alone, free-area flow: the wall time Yosys reports at the end
                      of the base run's synth.log files ("time: ..."), measured during the base
                      run (-j 19); no timing analysis, so it is not the cost of the predictive
                      number
  screen_synth_sta_s  the screening procedure that yields the synthesis-stage delay
                      (stages.synth.delay_ns): Yosys + ABC exactly as flow.synth, then OpenROAD
                      with flow.PNR_TCL up to `hwb_report synth` (OpenSTA), per circuit, library
                      and free flow, one statement order; wall and CPU (own + child processes)
  screen_orders_s     the same summed over k = 1, 3, 5 statement orders, on a subset
  screen_verify       the screening delay against stages.synth.delay_ns of the benchmark runs
  startup_s, checks_s process startup; the equivalence checks (not in the screening path)
  job_s               a whole job (synthesis, checks, placement, routing, extraction, timing,
                      power), from metrics.json (seconds), free-area flow, base run (-j 19)

The screening numbers come from results/screen_cost.json (committed; written by
--measure-screen or screen_cost.py, which says how the sample is drawn and what is timed), so the
default run runs no tools.  Circuits with G >= 400 are left out of the synthesis, screening and
job medians (they are not search candidates and take minutes).
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import statistics as st
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import harness as H  # noqa: E402
import features as FE  # noqa: E402
import bench  # noqa: E402
import screen_cost as SC  # noqa: E402
import manifest as M  # noqa: E402
from hwbench import design as D, platforms as P  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--measure-screen', type=int, metavar='N', default=0,
                    help='re-measure the screening on N circuits first (runs the tools)')
    ap.add_argument('--subset', type=int, default=20, help='circuits that get every order')
    ap.add_argument('--orders', type=int, default=5, help='statement orders on the subset')
    ap.add_argument('-j', '--jobs', type=int, default=4)
    ap.add_argument('--no-checks', action='store_true', help='do not time the checks')
    a = ap.parse_args(argv)
    if a.measure_screen:
        SC.measure(a.measure_screen, a.subset, a.orders, a.jobs, not a.no_checks)

    models = {pl: FE.lib_models(P.get(pl), P.get(pl).path(P.get(pl).lib).read_text())
              for pl in P.PLATFORMS}
    files = [str(f) for f in bench.expand(bench.suite('all'))]
    for name in ('sample.json', 'screen.json'):
        files += [str(H.HERE.parents[1] / e['file']) for e in json.loads((HERE / name).read_text())['candidates']]
    ft = []
    for f in files:
        d = D.load(f)
        if d.metrics['G'] >= 400:
            continue
        t = time.perf_counter()
        FE.features(d, models)
        ft.append(time.perf_counter() - t)
    syn, job = [], []
    for j in M.jobs(('base',)):
        if j.flow != 'free-area':
            continue
        mf = M.metrics_file(j)
        r = json.loads(mf.read_text())
        if r['metrics']['G'] >= 400:
            continue
        job.append(r['seconds'])
        m = re.search(r'time: ([\d.]+)s, user', (mf.parent / 'synth.log').read_text())
        if m:
            syn.append(float(m.group(1)))
    q = SC.q
    out = {'features_s': {'n': len(ft), 'median': st.median(ft), 'p10': q(ft, .1), 'p90': q(ft, .9)},
           'synthesis_only_s': {'n': len(syn), 'median': st.median(syn), 'p90': q(syn, .9),
                                'what': 'Yosys + ABC wall time from synth.log, free-area flow, '
                                        'base run (-j 19); no timing analysis'}}
    if SC.OUT.exists():
        out.update(SC.summarize(json.loads(SC.OUT.read_text())))
    out['job_s'] = {'n': len(job), 'median': st.median(job), 'p90': q(job, .9),
                    'what': 'whole job (metrics.json seconds), free-area flow, base run (-j 19)'}
    (pathlib.Path(os.environ.get('HWRESEARCH_RESULTS', HERE / 'results')) / 'timing.json').write_text(json.dumps(out, indent=1) + '\n')
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
