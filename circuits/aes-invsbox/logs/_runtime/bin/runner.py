#!/usr/bin/env python3
"""One CPU's job loop: claim the next job of queue.jsonl (flock), run invconjpull.py on it, repeat until
the deadline.  The queue is shared by all runners, so no CPU waits for another; past its end the queue
repeats with new seeds.

    python3 runner.py --dir CONJDIR --end EPOCH --name NAME
"""
import argparse
import fcntl
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAMP = HERE.parent
REPO = Path(os.environ.get('XCR_REPO', str(Path.home() / 'xcr-boolflux')))

ap = argparse.ArgumentParser()
ap.add_argument('--dir', required=True)
ap.add_argument('--end', type=float, required=True)
ap.add_argument('--name', required=True)
ap.add_argument('--margin', type=float, default=90, help='seconds kept free before the deadline')
ap.add_argument('--min-job', type=float, default=180, help='no new job with less time than this')
a = ap.parse_args()
D = Path(a.dir)
queue = [json.loads(l) for l in (D / 'queue.jsonl').read_text().splitlines() if l.strip()]
(D / 'jobs').mkdir(exist_ok=True)
log = open(D / ('runner-%s.log' % a.name), 'a')


def say(*x):
    log.write('%s %s\n' % (time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), ' '.join(map(str, x)))); log.flush()


def claim():
    with open(D / 'queue.lock', 'a+') as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        nf = D / 'next.txt'
        k = int(nf.read_text()) if nf.exists() else 0
        nf.write_text(str(k + 1))
    return k


env = dict(os.environ, XS_INVSBOX='1', PYTHONPATH=str(CAMP / 'shim'),
           BOOLFLUX_CACHE=os.environ.get('BOOLFLUX_CACHE', str(Path.home() / '.cache' / 'boolflux')))
say('runner start, deadline', time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(a.end)))
while True:
    rem = a.end - time.time() - a.margin
    if rem < a.min_job:
        say('deadline: %.0f s left, no new job' % (rem + a.margin)); break
    k = claim()
    j = dict(queue[k % len(queue)])
    rep = k // len(queue)
    seed = j['seed'] + 100000 * rep
    secs = int(min(j['seconds'], rem))
    tag = '%04d-r%d-a%d-ad%d-g%d-gd%d-%s' % (k, j['round'] + rep * 100, *j['start_tuple'],
                                             j['conj'].replace(':', '').replace(',', '_')[:40])
    jd = D / 'jobs' / tag
    jd.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, str(HERE / 'invconjpull.py'), '--in', j['start'], '--target', j['start'],
           '--seed', str(seed), '--seconds', str(secs), '--out', str(jd), '--conj', j['conj'],
           '--schedule', j['schedule'], '--repair-keep', 'alt',
           '--screen-cache', str(CAMP / 'cache' / 'conj3')]
    (jd / 'job.json').write_text(json.dumps({'queue_index': k, 'repeat': rep, 'job': j, 'seed': seed, 'seconds': secs,
                                             'runner': a.name, 'cmd': cmd, 'env': {'XS_INVSBOX': '1', 'PYTHONPATH': env['PYTHONPATH']},
                                             'cwd': str(REPO), 'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=1) + '\n')
    t0 = time.time()
    say('job', k, tag, 'seconds', secs)
    with open(jd / 'stdout.log', 'a') as lf:
        try:
            rc = subprocess.run(cmd, cwd=str(REPO), env=env, stdout=lf, stderr=subprocess.STDOUT,
                                timeout=secs + 150).returncode
        except subprocess.TimeoutExpired:
            rc = 'timeout'
    n = len(list(jd.glob('conjpull-*.circ.txt')))
    say('done', k, 'rc', rc, 'written', n, '%.0fs' % (time.time() - t0))
say('runner end')
