#!/usr/bin/env python3
"""Run a list of erun.py jobs, one process per CPU (pinned), and print a paired summary.

    python3 batch.py PLAN.json OUTDIR [--cpus 5,6,7,8,9]
PLAN.json: list of {"tag", "start", "seed", "seconds", "arm", "caps": {"A","AD","GD"}, "set": [..], "objective"}
"""
import json, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def cmd(job, out):
    kick = job['arm'] == 'kick'
    c = ['python3', str(HERE / ('kick.py' if kick else 'erun.py')), '--start', job['start'], '--out', str(out),
         '--tag', job['tag'], '--seed', str(job['seed']), '--seconds', str(job['seconds']),
         '--objective', job.get('objective', 'cost,gd')]
    if not kick: c += ['--arm', job['arm']]
    for k, f in (('A', '--cap-a'), ('AD', '--cap-ad'), ('GD', '--cap-gd')):
        v = job.get('caps', {}).get(k)
        if v is not None: c += [f, str(v)]
    for s in job.get('set', []):
        if kick:
            k, v = s.split('=', 1); c += ['--' + k, v]
        else:
            c += ['--set', s]
    if job.get('bin'): c += ['--bin', job['bin']]
    return c


def main():
    plan = json.loads(Path(sys.argv[1]).read_text()); out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    cpus = [5, 6, 7, 8, 9]
    if '--cpus' in sys.argv: cpus = [int(x) for x in sys.argv[sys.argv.index('--cpus') + 1].split(',')]
    queue = [j for j in plan if not (out / (j['tag'] + '.json')).exists()]
    free = list(cpus); running = []
    while queue or running:
        while queue and free:
            j = queue.pop(0); cpu = free.pop(0)
            lf = open(out / (j['tag'] + '.driver.log'), 'w')
            p = subprocess.Popen(['taskset', '-c', str(cpu)] + cmd(j, out), stdout=lf, stderr=subprocess.STDOUT)
            running.append((p, cpu, lf, j))
        time.sleep(0.5)
        for r in list(running):
            if r[0].poll() is not None:
                r[2].close(); running.remove(r); free.append(r[1])
    print('done', len(plan))


if __name__ == '__main__':
    main()
