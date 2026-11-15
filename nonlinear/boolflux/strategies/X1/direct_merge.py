#!/usr/bin/env python3
"""Direct measure of the hub operator x1_merge on a copy of an archive (no scheduler, no bandit):
N consecutive jobs, candidates verified and admitted exactly as the scheduler does (Archive.admit).

    python3 direct_merge.py CAMPAIGN_COPY JOBS SECONDS_PER_JOB
Writes CAMPAIGN_COPY/x1_direct.jsonl (one line per job) and prints a summary."""
import json, random, subprocess, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from boolflux.hub.archive import Archive
from boolflux.hub.common import metrics
from boolflux import core

d = Path(sys.argv[1]); jobs = int(sys.argv[2]); secs = float(sys.argv[3])
op = HERE.parents[1] / 'hub' / 'ops' / 'x1_merge.py'
ar = Archive(d); rng = random.Random(5); tot = {'jobs': 0, 'cands': 0, 'admitted': 0, 'gain': 0.0, 'cpu_s': 0.0}
pts = []
for j in range(jobs):
    tid = rng.choice(ar.front_ids()); jd = d / 'jobs' / ('x1d-%03d' % j)
    subprocess.run([sys.executable, str(op), '--archive', str(d), '--in', tid, '--seed', str(100 + j), '--seconds', str(secs), '--out', str(jd)])
    rec = json.loads((jd / 'record.json').read_text())
    out = []
    for f in sorted(jd.glob('cand-*.bfx')):
        c = core.from_kernel(f.read_text(), f.stem)
        st, r, g = ar.admit(c, parents=[tid], operator='x1_merge', settings={}, seed=100 + j, run_id=jd.name,
                            code_version=rec.get('code_version'), cpu_s=rec.get('cpu_s'), wall_s=rec.get('wall_s'))
        out.append({'m': metrics(c), 'status': st, 'gain': g})
        if st == 'admitted':
            tot['admitted'] += 1; tot['gain'] += g
            if g >= 1: pts.append((metrics(c), g))
    tot['jobs'] += 1; tot['cands'] += len(out); tot['cpu_s'] += rec.get('cpu_s') or 0
    line = {'job': j, 'target': tid, 'cpu_s': rec.get('cpu_s'), 'scanned': rec['info']['scanned'], 'hits_total': rec['info']['hits_total'],
            'polished': rec['info']['polished'], 'outcome': out, 'ts': time.time()}
    with open(d / 'x1_direct.jsonl', 'a') as fh: fh.write(json.dumps(line) + '\n')
    print(j, 'cpu', rec.get('cpu_s'), 'scanned', rec['info']['scanned'], 'cands', len(out), 'admitted', sum(o['status'] == 'admitted' for o in out),
          'gain', round(sum(o['gain'] for o in out if o['status'] == 'admitted'), 2), [p['result'] for p in rec['info']['polished']], flush=True)
print('TOTAL', tot, 'frontier points (gain >= 1):', pts)
