#!/usr/bin/env python3
"""T3: GF(4)-coordinate move pipeline. For each choice of 4 GF(4)-points (from a gf4search JSON, or
random admissible ones), build the circuit (gf4build, keep2 and/or fresh region 2), polish with the
kernel (caps, objective cost,gd), verify, log jsonl; keep results meeting the target in found/.
    gf4pipe.py SRC --json SEARCH.json --out DIR [--from K --step S] [--seconds 100] [--mode keep2|fresh|both]
               [--caps 35,3,-] [--hours H]"""
import argparse
import json
import random
import sys
import time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core                                         # noqa: E402
from boolflux.hub import ops as O                                 # noqa: E402
from boolflux.hub.common import load, metrics, verify, cid, code_version   # noqa: E402
from gf4build import build                                        # noqa: E402

MODEL = core.Model.load('nist')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('--json'); ap.add_argument('--out', required=True)
    ap.add_argument('--from', dest='frm', type=int, default=0); ap.add_argument('--step', type=int, default=1)
    ap.add_argument('--seconds', type=float, default=100); ap.add_argument('--mode', default='keep2')
    ap.add_argument('--caps', default='35,3,-'); ap.add_argument('--target', default='35,3,138,26')
    ap.add_argument('--hours', type=float, default=1.0); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--points', help='explicit list a,b,c,d;e,f,g,h')
    a = ap.parse_args()
    out = Path(a.out); (out / 'found').mkdir(parents=True, exist_ok=True); (out / 'res').mkdir(exist_ok=True)
    c = load(a.src)
    A, AD, GD = (None if x == '-' else int(x) for x in a.caps.split(','))
    tA, tAD, tG, tGD = (int(x) for x in a.target.split(','))
    if a.points:
        choices = [[int(x) for x in p.split(',')] for p in a.points.split(';')]
    else:
        choices = [r[4] for r in json.load(open(a.json))['res']]
    choices = choices[a.frm::a.step]
    modes = ['keep2', 'fresh'] if a.mode == 'both' else [a.mode]
    log = open(out / 'pipe.jsonl', 'a'); t_end = time.time() + 3600 * a.hours; ver = code_version()
    for pts in choices:
        for mode in modes:
            if time.time() > t_end: return
            try:
                nc = build(c, pts, keep2=(mode == 'keep2'))
            except Exception as e:
                log.write(json.dumps({'points': pts, 'mode': mode, 'error': str(e)}) + '\n'); log.flush(); continue
            m1 = metrics(nc)
            job = out / 'jobs' / ('%s-%s' % ('-'.join(map(str, pts)), mode)); job.mkdir(parents=True, exist_ok=True)
            cands, info = O._kernel(nc, {'A': A, 'AD': AD, 'GD': GD}, 'cost,gd', a.seed, a.seconds, job, out)
            rec = {'points': pts, 'mode': mode, 'built': m1, 'seconds': a.seconds, 'src': a.src, 'code': ver}
            if cands:
                r = cands[0]; m = metrics(r); ok, vi = verify(r); rec.update({'m': m, 'ok': ok})
                k = cid(r)
                (out / 'res' / ('a%d-ad%d-g%d-gd%d-%s.bfx' % (m + (k,)))).write_text(core.to_kernel(r))
                if ok and m[0] <= tA and m[1] <= tAD and m[2] <= tG and m[3] <= tGD:
                    name = 'aes-sbox-a%d-ad%d-g%d-gd%d-%s' % (m + (k,))
                    (out / 'found' / (name + '.circ.txt')).write_text(core.write_ncff(r, MODEL))
                    (out / 'found' / (name + '.json')).write_text(json.dumps({
                        'metrics': m, 'made_by': 'strategies/T3/gf4pipe.py: GF(4)-coordinate move (gf4build) + kernel polish',
                        'source': a.src, 'points': pts, 'mode': mode, 'seed': a.seed, 'seconds': a.seconds,
                        'caps': a.caps, 'code_version': ver, 'time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=1))
                    rec['found'] = name
            try:
                (job / 'kernel.log').write_text('\n'.join((job / 'kernel.log').read_text().splitlines()[-10:]))
            except Exception:
                pass
            log.write(json.dumps(rec) + '\n'); log.flush()


if __name__ == '__main__':
    main()
