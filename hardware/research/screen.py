#!/usr/bin/env python3
"""Prospective test of a cheap hardware-aware score: screen whole same-metric pools, then
benchmark the predicted best, the predicted worst and a random draw.

    python3 hardware/research/screen.py            # candidates/screen/, screen.json, lists/screen.txt

The score is fixed before any of these circuits is benchmarked: ``f_sta_nangate45`` of
features.py (the load-aware longest path with delays fitted on the Liberty tables, no fitting on
benchmark results).  Pools: per function, the same-metric groups with at least MIN_POOL
distinct structures in the inventory (largest first, at most 2 per function), minus every
circuit already benchmarked.  It was run on the folded-hash inventory (pool.jsonl.gz); like
sample.py it needs the local campaign archives.  From each pool: TOP lowest scores, TOP highest, TOP uniform random
(seed SEED), disjoint.
"""
from __future__ import annotations

import collections
import concurrent.futures as cf
import gzip
import json
import pathlib
import random
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import harness  # noqa: E402,F401  (candidate origin)
import features as FE  # noqa: E402
import sample as S  # noqa: E402
from hwbench import design as D, platforms as P  # noqa: E402

SEED = 20261119
MIN_POOL = 200
PER_FUNCTION = 2
TOP = 10
OUTDIR = HERE / 'candidates' / 'screen'
_M = {}


def models():
    if not _M:
        _M.update({pl: FE.lib_models(P.get(pl), P.get(pl).path(P.get(pl).lib).read_text())
                   for pl in P.PLATFORMS})
    return _M


def score(args):
    e, tmp = args
    p = tmp / (S.name_for(e) + '.circ.txt')
    try:
        S.write_candidate(e, p)
        d = D.load(p)
        f = FE.features(d, models())
        return e['hash'], f['sta_nangate45'], f['sta_sky130hd'], None
    except Exception as ex:
        return e['hash'], None, None, str(ex)[:100]
    finally:
        p.unlink(missing_ok=True)


def main():
    rng = random.Random(SEED)
    pool = [json.loads(l) for l in gzip.open(HERE / 'inventory' / 'pool.jsonl.gz', 'rt')]
    done = {e['hash'] for e in json.loads((HERE / 'sample.json').read_text())['candidates']}
    import inventory as I
    import bench
    for f in bench.expand(bench.suite('all')):
        done.add(I.read_boolean(str(f))['hash'])
    groups = collections.defaultdict(list)
    for e in pool:
        if e['hash'] not in done:
            groups[(e['function'], S.key(e))].append(e)
    chosen_groups = []
    for fn in sorted({k[0] for k in groups}):
        ks = sorted((k for k in groups if k[0] == fn and len(groups[k]) >= MIN_POOL),
                    key=lambda k: (-len(groups[k]), k))[:PER_FUNCTION]
        chosen_groups += ks
    tmp = HERE / 'build' / '_screen_tmp'
    tmp.mkdir(parents=True, exist_ok=True)
    if OUTDIR.exists():
        shutil.rmtree(OUTDIR)
    OUTDIR.mkdir(parents=True)
    report, lines = [], []
    with cf.ProcessPoolExecutor() as ex:
        for k in chosen_groups:
            es = sorted(groups[k], key=lambda e: e['hash'])
            scored = {}
            fails = 0
            for h, s1, s2, err in ex.map(score, [(e, tmp) for e in es], chunksize=64):
                if err:
                    fails += 1
                else:
                    scored[h] = (s1, s2)
            ranked = sorted(scored, key=lambda h: (scored[h][0], h))
            top, bottom = ranked[:TOP], ranked[-TOP:]
            rest = [h for h in ranked[TOP:-TOP]]
            rand = rng.sample(rest, TOP)
            byh = {e['hash']: e for e in es}
            for tag, hs in (('top', top), ('bottom', bottom), ('random', rand)):
                for h in hs:
                    e = dict(byh[h], part='screen-' + tag, score=scored[h])
                    d = OUTDIR / e['function']
                    d.mkdir(exist_ok=True)
                    p = d / (S.name_for(e) + '.circ.txt')
                    S.write_candidate(e, p)
                    e['file'] = p.relative_to(HERE.parents[1]).as_posix()
                    lines.append(e['file'])
                    report.append(e)
            vals = sorted(v[0] for v in scored.values())
            print(k, 'pool', len(es), 'scored', len(scored), 'failed', fails,
                  'score range %.4f-%.4f' % (vals[0], vals[-1]))
    shutil.rmtree(tmp, ignore_errors=True)
    (HERE / 'screen.json').write_text(json.dumps({'seed': SEED, 'score': 'f_sta_nangate45',
                                                  'groups': [list(map(str, k)) for k in chosen_groups],
                                                  'candidates': report}, indent=1) + '\n')
    (HERE / 'lists' / 'screen.txt').write_text('\n'.join(lines) + '\n')
    print(len(lines), 'screen candidates')


if __name__ == '__main__':
    main()
