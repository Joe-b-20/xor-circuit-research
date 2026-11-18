#!/usr/bin/env python3
"""What the scores cost (-> results/timing.json).

    python3 hardware/research/timing.py

  features   wall time of features.features() per circuit (all three scores, both libraries),
             over every candidate and baseline circuit, on one core
  synthesis  Yosys + ABC time of the free-area flow, from the base run's synth.log files
  job        a whole job (synthesis, checks, placement, routing, extraction, timing, power), from
             metrics.json (seconds), free-area flow
Circuits with G >= 400 are left out of the synthesis and job medians (they are not search
candidates and take minutes).
"""
from __future__ import annotations

import json
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
from hwbench import design as D, platforms as P  # noqa: E402


def main():
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
    for mf in (H.RBUILD / 'base').glob('*/*/free-area/metrics.json'):
        r = json.loads(mf.read_text())
        if r['metrics']['G'] >= 400:
            continue
        job.append(r['seconds'])
        m = re.search(r'time: ([\d.]+)s, user', (mf.parent / 'synth.log').read_text())
        if m:
            syn.append(float(m.group(1)))
    q = lambda v, x: sorted(v)[int(x * (len(v) - 1))]
    out = {'features_s': {'n': len(ft), 'median': st.median(ft), 'p10': q(ft, .1), 'p90': q(ft, .9)},
           'synthesis_s': {'n': len(syn), 'median': st.median(syn), 'p90': q(syn, .9)},
           'job_s': {'n': len(job), 'median': st.median(job), 'p90': q(job, .9)}}
    (HERE / 'results' / 'timing.json').write_text(json.dumps(out, indent=1) + '\n')
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
