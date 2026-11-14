"""llay calibration: recover a valid last layer over a fixed E after re-randomising r of the
published last-layer slots (r = 13: from scratch).  Prints one JSON line per run and appends to
~/xs-campaigns/2026-11-14-G/ll/calib.jsonl.

usage: python3 calib_ll.py PROB SRC_CIRCUIT K R SEEDS SECS [llay k=v ...]
"""
from __future__ import annotations

import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
D = Path(os.path.expanduser('~/xs-campaigns/2026-11-14-G/ll'))


def main():
    prob, src, K, R, seeds, secs = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5], float(sys.argv[6])
    extra = sys.argv[7:]
    a, b = (seeds.split('-') + [seeds])[:2]
    full = Path(D / ('init-full-%s.txt' % Path(src).stem))
    if not full.exists():
        subprocess.run([sys.executable, str(HERE / 'll_prob.py'), 'init', '--l1', src, '--inv', src, '--sol', src,
                        '--out', str(full)], check=True, stdout=subprocess.DEVNULL)
    rows = full.read_text().split('\n')[1:]
    rows = [r for r in rows if r.strip()]
    for s in range(int(a), int(b) + 1):
        rng = random.Random(1000 * R + s)
        keep = sorted(rng.sample(range(len(rows)), max(0, min(len(rows), K) - R))) if R < K else []
        init = D / ('init-r%d-s%d-%s.txt' % (R, s, Path(prob).stem))
        init.write_text('init K %d\n' % len(keep) + ''.join(rows[i] + '\n' for i in keep), encoding='utf-8', newline='\n')
        pre = D / ('cal-%s-r%d-s%d' % (Path(prob).stem, R, s))
        for ext in ('.log', '.best', '.sol'):
            p = Path(str(pre) + ext)
            if p.exists(): p.unlink()
        t0 = time.time()
        subprocess.run([str(HERE / 'llay'), prob, str(pre), str(s), str(secs), 'init=%s' % init] + extra)
        dt = time.time() - t0
        log = Path(str(pre) + '.log').read_text()
        best = None
        for line in log.split('\n'):
            if ' best ' in line:
                best = int(line.split(' best ')[1].split()[0])
        solved = Path(str(pre) + '.sol').exists()
        out = {'prob': Path(prob).name, 'K': K, 'R': R, 'seed': s, 'solved': solved, 'secs': round(dt, 1),
               'best': 0 if solved else best, 'extra': extra}
        print(json.dumps(out), flush=True)
        with open(D / 'calib.jsonl', 'a') as f: f.write(json.dumps(out) + '\n')


if __name__ == '__main__':
    main()
