#!/usr/bin/env python3
"""Screen the 2040 conjugates of a circuit (conj.py) by re-synthesising the top linear layer with the
Boyar-Peralta heuristic (strategies/T2/bp.py, exact distances, depth unconstrained), then the bottom
(output) layer of the best ones with BP + trb.  Writes OUT/screen.jsonl and the best circuits.

    conj2.py FILE --out DIR [--top-runs 6] [--nbest 40] [--bot-runs 4] [--lams 1-255] [--ks 0-7]
"""
import json, random, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
sys.path.append(str(HERE.parent / 'F')); sys.path.append(str(HERE.parent / 'T2'))
import conj as CJ  # noqa
import bp  # noqa
from boolflux import core  # noqa


def arg(a, k, d, f=str):
    return f(a[a.index(k) + 1]) if k in a else d


def rng_(s):
    lo, hi = map(int, s.split('-')); return range(lo, hi + 1)


def opt(c, region, runs, rng, D=99):
    best, info = bp.optimise(c, D, region, rng, runs, log=lambda *x: None)
    return best if best is not None else c


def main():
    a = sys.argv[1:]
    f = a[0]; out = Path(arg(a, '--out', 'conj2')); out.mkdir(parents=True, exist_ok=True)
    top_runs = arg(a, '--top-runs', 6, int); nbest = arg(a, '--nbest', 40, int); bot_runs = arg(a, '--bot-runs', 4, int)
    lams = rng_(arg(a, '--lams', '1-255')); ks = rng_(arg(a, '--ks', '0-7'))
    c = CJ.BT.load(f)
    t0 = time.time()
    log = open(out / 'screen.jsonl', 'a')
    res = []
    for k in ks:
        for lam in lams:
            cc = CJ.conj_circuit(c, lam, k)
            r = opt(cc, 'top', top_runs, random.Random(lam * 8 + k))
            m = r.metrics(CJ.MODEL)
            rec = {'stage': 'top', 'lam': lam, 'k': k, 'G': m['G'], 'GD': m['GD'], 'naive': len(cc.gates)}
            log.write(json.dumps(rec) + '\n'); log.flush()
            res.append((m['G'], m['GD'], lam, k, r))
        print('k %d %.0fs best %s' % (k, time.time() - t0, sorted(r_[:4] for r_ in res)[:3]), flush=True)
    res.sort(key=lambda t: t[:2])
    fin = []
    for G, GD, lam, k, r in res[:nbest]:
        rr = opt(r, 'bottom', bot_runs, random.Random(lam * 8 + k + 1))
        rr = CJ.resynth(rr, random.Random(lam), 1)
        assert rr.value_table() == CJ.AES
        m = rr.metrics(CJ.MODEL)
        rec = {'stage': 'bottom', 'lam': lam, 'k': k, 'G': m['G'], 'GD': m['GD'], 'G_top': G}
        log.write(json.dumps(rec) + '\n'); log.flush()
        fin.append((m['G'], m['GD'], lam, k, rr))
        name = 'conj-l%d-k%d-g%d-gd%d.circ.txt' % (lam, k, m['G'], m['GD'])
        (out / name).write_text(core.write_ncff(rr, CJ.MODEL, comments=[
            'P3 conj2.py of %s: conjugate lam %d k %d, BP top + BP/trb bottom resynthesis' % (f, lam, k)]))
    fin.sort(key=lambda t: t[:2])
    print('final', [t[:4] for t in fin[:20]], '%.0fs' % (time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
