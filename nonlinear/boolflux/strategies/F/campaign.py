#!/usr/bin/env python3
"""Track-F campaign runner: a queue of fdrive jobs over CPUs 1-4, one pinned job per CPU.

    python3 campaign.py PLAN.json OUTDIR [--cpus 1,2,3,4]

PLAN = {"jobs": [{"name": ..., "start": FILE | "BEST:<cap>", "cap": 14, "mode": "gate", "seconds": 3600,
                  "seed": 1, "args": [...]}, ...]}
"BEST:<cap>" = the best feasible circuit for that cap found so far by this campaign's finished jobs
(or the file given in PLAN["best_init"][cap]).  Jobs whose OUTDIR/<name>/done exists are skipped.
Every new best per cap is copied to OUTDIR/best-gd<cap>.circ.txt and listed in OUTDIR/bests.jsonl.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2])); sys.path.insert(0, str(HERE))
from boolflux import core   # noqa: E402


def gcount(p):
    c = core.read_ncff(str(p)); m = c.metrics(); return m['G'], m['GD'], m['AD']


def main():
    plan = json.loads(Path(sys.argv[1]).read_text()); out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    cpus = [int(x) for x in sys.argv[sys.argv.index('--cpus') + 1].split(',')] if '--cpus' in sys.argv else [1, 2, 3, 4]
    best = {str(k): v for k, v in plan.get('best_init', {}).items()}
    for k in list(best):
        bp = out / ('best-%s.circ.txt' % k)
        if bp.exists(): best[k] = str(bp)
    queue = [j for j in plan['jobs'] if not (out / j['name'] / 'done').exists()]
    running = {}
    def harvest(j):
        bp = out / j['name'] / 'best.circ.txt'
        if not bp.exists(): return
        G, GD, AD = gcount(bp); cap = j['cap']; line = str(j.get('line', cap))
        if GD > cap: return
        cur = best.get(line)
        if cur is None or G < gcount(cur)[0]:
            dst = out / ('best-%s.circ.txt' % line)
            dst.write_text(bp.read_text()); best[line] = str(dst)
            # every new campaign best goes through aes_check into found/ with a sidecar
            try:
                cmd = (out / j['name'] / 'cmd.txt').read_text().strip()
                envj = (out / j['name'] / 'env.json').read_text().strip()
                subprocess.run([sys.executable, str(HERE / 'record.py'), str(bp), 'camp-%s-%s' % (out.name, j['name']),
                                '--start', j['start'], '--command', cmd + '  env ' + envj, '--seed', str(j['seed']),
                                '--config', 'fdrive mode %s cap %d' % (j['mode'], cap),
                                '--time', 'see %s/log.jsonl' % (out / j['name']),
                                '--mechanism', 'fdrive %s' % j['mode']], capture_output=True, timeout=600)
            except Exception as e:
                print('record failed', e, flush=True)
            with open(out / 'bests.jsonl', 'a') as f:
                f.write(json.dumps({'utc': time.strftime('%H:%M:%S', time.gmtime()), 'cap': cap, 'line': line, 'G': G, 'GD': GD,
                                    'job': j['name'], 'mode': j['mode']}) + '\n')
    while queue or running:
        for cpu in cpus:
            p = running.get(cpu)
            if p is not None and p[0].poll() is not None:
                (out / p[1]['name'] / 'done').write_text('rc %s\n' % p[0].returncode)
                harvest(p[1]); running.pop(cpu)
            if cpu not in running and queue:
                j = queue.pop(0)
                st = j['start']
                if st.startswith('BEST:'): st = best[st[5:]]
                jd = out / j['name']; jd.mkdir(exist_ok=True)
                cmd = ['taskset', '-c', str(cpu), sys.executable, str(HERE / 'fdrive.py'), '--start', st,
                       '--cap', str(j['cap']), '--mode', j['mode'], '--seconds', str(j['seconds']),
                       '--seed', str(j['seed']), '--out', str(jd)] + j.get('args', [])
                (jd / 'cmd.txt').write_text(' '.join(cmd) + '\n')
                import os
                env = dict(os.environ); env.update(j.get('env', {}))
                (jd / 'env.json').write_text(json.dumps(j.get('env', {})) + '\n')
                running[cpu] = (subprocess.Popen(cmd, stdout=open(jd / 'stdout.txt', 'w'), stderr=subprocess.STDOUT, env=env), j)
                print(time.strftime('%H:%M:%S', time.gmtime()), 'cpu', cpu, 'start', j['name'], st, flush=True)
        time.sleep(5)
    print('campaign done', flush=True)


if __name__ == '__main__':
    main()
