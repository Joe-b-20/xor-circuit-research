"""Campaign driver (track G): relaxed last-layer walks (llay multi-solution mode) alternating with
three-stage evaluation (eval3.py) of every new layer, until the deadline.

usage: python3 camp3.py NAME DEADLINE_EPOCH CONFIG.json
CONFIG: list of {"prob", "init", "tag", "slice", "l", "m", "args": [...]}
Output dir ~/xs-campaigns/2026-11-14-G/camp-NAME/ ; eval records in camp-NAME/eval.jsonl
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


def main():
    name, deadline, cfgp = sys.argv[1], float(sys.argv[2]), sys.argv[3]
    cfgs = json.loads(Path(cfgp).read_text())
    rd = OUT / ('camp-' + name); rd.mkdir(parents=True, exist_ok=True)
    seed = (int(time.time()) + 7919 * sum(map(ord, name))) % 1000000
    i = 0
    while time.time() + 60 < deadline:
        cfg = cfgs[i % len(cfgs)]; i += 1; seed += 1
        secs = min(cfg.get('slice', 600), deadline - time.time() - 30)
        pre = rd / ('%s-s%d' % (cfg['tag'], seed))
        args = [str(HERE / 'llay'), cfg['prob'], str(pre), str(seed), str(secs), 'multi=1',
                'maxsol=%d' % cfg.get('maxsol', 400), 'report=120']
        if cfg.get('init'): args.append('init=' + cfg['init'])
        args += cfg.get('args', [])
        subprocess.run(args)
        nsol = len(list(rd.glob(pre.name + '.sol*')))
        rec = {'tag': cfg['tag'], 'seed': seed, 'nsol': nsol, 'utc': time.strftime('%H:%M:%S', time.gmtime())}
        best = None
        try:
            for line in Path(str(pre) + '.log').read_text().split('\n'):
                if ' best ' in line: best = int(line.split(' best ')[1].split()[0])
        except FileNotFoundError: pass
        rec['best'] = best
        with open(rd / 'walks.jsonl', 'a') as f: f.write(json.dumps(rec) + '\n')
        if nsol and time.time() + 60 < deadline:
            if cfg.get('eval') == 'eval_v':
                subprocess.run([sys.executable, str(HERE / 'eval_v.py'), '--sols', str(pre) + '.sol[0-9]*',
                                '--prob', cfg['prob'],
                                '--l', str(cfg.get('l', 9)), '--m', str(cfg.get('m', 5)), '--mid-secs', '5',
                                '--log', str(rd / 'eval.jsonl')], stdout=subprocess.DEVNULL)
            else:
                subprocess.run([sys.executable, str(HERE / 'eval3.py'), '--sols', str(pre) + '.sol[0-9]*',
                                '--l', str(cfg.get('l', 9)), '--m', str(cfg.get('m', 5)),
                                '--skip-cover-if-mid-fails', '--cover-limit', '600',
                                '--log', str(rd / 'eval.jsonl')], stdout=subprocess.DEVNULL)
            # keep disk use small: drop the per-solution 4-bit side files
            for p in rd.glob(pre.name + '.sol*.mid*'):
                try: p.unlink()
                except OSError: pass


if __name__ == '__main__':
    main()
