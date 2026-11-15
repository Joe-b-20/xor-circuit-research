#!/usr/bin/env python3
"""Overnight sweep: the deep2 recipe that turned hub A29 g134 into a new A28 (window = all last-level
ANDs + consumer closure of one interior AND; new ANDs = <= amax interior ANDs over span(x, kept)
then one parallel layer over span(x, kept, interior), every class mod span(1, x, kept) inside
Sigma_U; exact min-cover; improvement-only, |new| <= |U| - 1), applied to every A <= 29 circuit
of the given files, one representative per AND-structure family, with recursive descent: every
improved circuit is verified, saved, and queued again in the same shard.

Usage: deep2_sweep.py OUTDIR SHARD NSHARDS [--amax 1] [--pairs] [--maxnv 26] [--maxA 29] FILE_GLOB...
Files: NCFF (.circ.txt) or kernel (.bfx).  Logs: OUTDIR/sweep-SHARD-of-N.jsonl; circuits found:
OUTDIR/found/*.circ.txt + .json, each checked with campaigns/aes_check.py (field aes_check).
"""
import argparse
import glob
import itertools
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import deep2  # noqa: E402
import lay  # noqa: E402
from wsat import Base, Span, ONES, mklog  # noqa: E402

CHK = HERE.parents[1] / 'campaigns' / 'aes_check.py'


def _canon(vecs):
    sp = Span(vecs)
    vs = dict(sp.b)
    for h in sorted(vs):
        for k in vs:
            if k != h and (vs[k] >> h) & 1: vs[k] ^= vs[h]
    return hash(tuple(sorted(vs.values())))


def family_key(b):
    """X1b's structure test: span{1, x, AND tables} and the per-level spans (level <= L)."""
    base = [ONES] + b.tab[1:1 + b.n]
    L = max(b.level)
    return tuple(_canon(base + [b.andtab[k] for k in range(b.K) if b.level[k] <= l]) for l in range(1, L + 1))


def windows(b, pairs):
    sinks = {k for k in range(b.K) if not b.cons[k]}
    inner = [k for k in range(b.K) if b.cons[k]]
    Xs = [()] + list(itertools.combinations(inner, 1)) + (list(itertools.combinations(inner, 2)) if pairs else [])
    seen = set()
    for X in Xs:
        U = b.closure(set(X)) | sinks
        if frozenset(U) in seen: continue
        seen.add(frozenset(U))
        yield 'd' + '_'.join(map(str, X)), U


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('outdir'); ap.add_argument('shard', type=int); ap.add_argument('nshards', type=int)
    ap.add_argument('globs', nargs='+')
    ap.add_argument('--amax', type=int, default=1)
    ap.add_argument('--pairs', action='store_true')
    ap.add_argument('--maxnv', type=int, default=26)
    ap.add_argument('--maxA', type=int, default=29)
    ap.add_argument('--cap', type=int, default=200000)
    a = ap.parse_args()
    out = Path(a.outdir); (out / 'found').mkdir(parents=True, exist_ok=True)
    lay.FOUND = str(out / 'found')
    import chain; chain.FOUND = str(out / 'found')
    log = mklog(str(out / ('sweep-%d-of-%d.jsonl' % (a.shard, a.nshards))))
    files = sorted(set(f for g in a.globs for f in glob.glob(g)))
    # families (deterministic over all shards): first file of each family by (A, name)
    reps = {}
    for f in files:
        try: b = Base(f)
        except Exception as e:
            continue
        if b.K > a.maxA: continue
        k = family_key(b)
        if k not in reps or (b.K, f) < reps[k]: reps[k] = (b.K, f)
    work = sorted(reps.values())
    mine = [f for i, (A, f) in enumerate(work) if i % a.nshards == a.shard]
    log({'event': 'start', 'files': len(files), 'families': len(work), 'mine': len(mine), 'amax': a.amax,
         'pairs': a.pairs, 'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())})
    done_keys = set()
    while mine:
        path = mine.pop(0)
        b = Base(path)
        key = family_key(b)
        if key in done_keys: continue
        done_keys.add(key)
        for name, U in windows(b, a.pairs):
            nv = 8 + b.K - len(U)
            rec = {'method': 'deep2-sweep', 'src': path, 'A0': b.K, 'win': name, 'U': sorted(U), 'nv': nv,
                   'tag': 'sw-a%d-%s-%s' % (b.K, Path(path).stem[:14], name)}
            if nv > a.maxnv:
                rec['result'] = 'SKIP nv'; log(rec); continue
            t0 = time.time()
            try:
                deep2.run(b, U, rec, a.amax, a.cap)
            except Exception as e:
                rec['result'] = 'ERROR %r' % (e,)
            rec['time'] = round(time.time() - t0, 1)
            if rec.get('file'):
                pr = subprocess.run([sys.executable, str(CHK), rec['file']], capture_output=True, text=True)
                rec['aes_check'] = 'OK' if pr.returncode == 0 else 'FAIL'
                rec['aes_check_out'] = pr.stdout[-400:]
                if rec['aes_check'] == 'OK' and rec.get('A', 99) < b.K:
                    mine.insert(0, rec['file'])          # recursive descent on the improved circuit
            log(rec)
    log({'event': 'end', 'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())})


if __name__ == '__main__':
    main()
