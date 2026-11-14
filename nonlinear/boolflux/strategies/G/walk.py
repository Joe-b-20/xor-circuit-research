"""Long-run driver for llay walks (track G): cycles over configurations, each run SLICE seconds with
a fresh seed, until the deadline.  On a solution: builds the circuit, runs aes_check, and stores
NCFF + JSON sidecar + check output in ~/xs-campaigns/2026-11-14-G/found/.

usage: python3 walk.py NAME SLICE DEADLINE_EPOCH CONFIG.json
CONFIG: list of {"prob": path, "init": path|null, "inits1": path|null, "inv": circuit (joint) or
         null, "l1": circuit (non-joint), "args": [llay k=v ...], "tag": str}
Results: one JSON line per run in ~/xs-campaigns/2026-11-14-G/walk-NAME.jsonl
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = Path(os.path.expanduser('~/xs-campaigns/2026-11-14-G'))
FOUND = OUT / 'found'
CHECK = HERE.parents[1] / 'campaigns' / 'aes_check.py'


def parse_log(p):
    best = None; start = None
    for line in Path(p).read_text().split('\n'):
        if line.startswith('start'):
            start = int(line.split(' deficit ')[1].split()[0])
        if ' best ' in line:
            best = int(line.split(' best ')[1].split()[0])
    return start, best


def on_solution(cfg, pre, seed, t_run):
    FOUND.mkdir(parents=True, exist_ok=True)
    stem = 'G-%s-s%d-%d' % (cfg['tag'], seed, int(time.time()))
    circ = FOUND / (stem + '.circ.txt')
    cmd = [sys.executable, str(HERE / 'll_prob.py'), 'build', '--sol', str(pre) + '.sol', '--out', str(circ)]
    if cfg.get('inv') and cfg.get('joint'):
        cmd += ['--inv', cfg['inv'], '--joint', '1']
    else:
        cmd += ['--l1', cfg['l1'], '--inv', cfg['inv']]
    b = subprocess.run(cmd, capture_output=True, text=True)
    chk = subprocess.run([sys.executable, str(CHECK), str(circ)], capture_output=True, text=True)
    (FOUND / (stem + '.check.txt')).write_text(b.stdout + b.stderr + chk.stdout + chk.stderr)
    side = {'method': 'track G llay exact coordinate-descent walk', 'config': cfg, 'seed': seed,
            'time_utc': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()), 'run_secs': t_run,
            'build': b.stdout.strip(), 'check_rc': chk.returncode}
    (FOUND / (stem + '.json')).write_text(json.dumps(side, indent=1))
    return side


def main():
    name, slice_s, deadline, cfgp = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
    cfgs = json.loads(Path(cfgp).read_text())
    rd = OUT / ('walk-' + name); rd.mkdir(parents=True, exist_ok=True)
    seed = int(time.time()) % 100000
    i = 0
    while time.time() + 30 < deadline:
        cfg = cfgs[i % len(cfgs)]; i += 1; seed += 1
        secs = min(slice_s, deadline - time.time() - 10)
        pre = rd / ('%s-s%d' % (cfg['tag'], seed))
        args = [str(HERE / 'llay'), cfg['prob'], str(pre), str(seed), str(secs)]
        if cfg.get('init'): args.append('init=' + cfg['init'])
        if cfg.get('inits1'): args.append('inits1=' + cfg['inits1'])
        args += cfg.get('args', [])
        t0 = time.time()
        subprocess.run(args)
        dt = time.time() - t0
        start, best = parse_log(str(pre) + '.log')
        solved = Path(str(pre) + '.sol').exists()
        rec = {'tag': cfg['tag'], 'seed': seed, 'secs': round(dt), 'start': start, 'best': 0 if solved else best,
               'solved': solved, 'utc': time.strftime('%H:%M:%S', time.gmtime())}
        if solved:
            rec['found'] = on_solution(cfg, pre, seed, dt)
        with open(OUT / ('walk-%s.jsonl' % name), 'a') as f: f.write(json.dumps(rec) + '\n')
        print(json.dumps(rec), flush=True)


if __name__ == '__main__':
    main()
