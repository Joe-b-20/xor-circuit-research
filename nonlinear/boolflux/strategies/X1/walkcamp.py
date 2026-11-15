#!/usr/bin/env python3
"""X1 walk campaign (one process = one CPU; unattended, memory < 200 MB).

    python3 walkcamp.py OUT_DIR --hours H [--slice 600] [--shard K] [--target 27] [--adcap-prob P] --starts FILE...   (--starts last)

Loop until the time is over: pick a start circuit (the given files, plus circuits this campaign made:
lower-A results and dumped same-A circuits with a new product span, OUT_DIR/pool/), pick walk parameters
from a small table, run bfw (bfw.c) for --slice seconds, then
  - every result with fewer ANDs than its start is checked with campaigns/aes_check.py (two verifiers,
    256 inputs) and saved to OUT_DIR/found/ (.bfx, .circ.txt, .json sidecar);
  - up to 12 same-A circuits with new product spans are verified and stored in OUT_DIR/pool/ as further
    starts (the walk's sideways moves are kept across runs).
Start choice: lowest A first (70 %), fewest runs first within an A; otherwise uniform.
Log: OUT_DIR/runs-<shard>.jsonl (start, parameters, seed, best A, spans seen), OUT_DIR/camp-<shard>.log.
Success = a file found/aes-sbox-a27-* (or lower); the log line starts with "TARGET".
"""
import json, random, sys, time, hashlib
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[1] / 'campaigns'))
import x1lib as X, x1walkc as W
import aes_check
from boolflux.hub.common import load, metrics, sbox, MODEL, code_version
from boolflux import core

PARAMS = [  # plus, psplit, horizon, redec, pmerge
    (1, 0.02, 20000, 0.2, 1.0), (2, 0.05, 5000, 0.2, 1.0), (2, 0.05, 5000, 0.3, 0.05), (1, 0.05, 5000, 0.2, 0.05),
    (3, 0.05, 20000, 0.3, 0.2), (2, 0.02, 20000, 0.2, 0.01), (1, 0.02, 2000, 0.2, 0.2), (3, 0.1, 5000, 0.2, 0.05)]


def main():
    a = sys.argv[1:]
    out = Path(a[0])
    def opt(name, d): return type(d)(a[a.index(name) + 1]) if name in a else d
    hours = opt('--hours', 1.0); slc = opt('--slice', 600.0); shard = opt('--shard', 0); target = opt('--target', 27)
    adcap_prob = opt('--adcap-prob', 0.0)       # share of runs that keep the start's AND depth (bfw adcap)
    starts = a[a.index('--starts') + 1:] if '--starts' in a else []
    for d in ('found', 'pool', 'work'): (out / d).mkdir(parents=True, exist_ok=True)
    rng = random.Random(1000 + shard)
    bb = W.binary(out / "work"); W.binary = lambda o: bb        # one binary per campaign directory and source version
    lf = open(out / ('camp-%d.log' % shard), 'a')
    def log(*x):
        s = ' '.join(str(v) for v in x); print(s, flush=True); lf.write(time.strftime('%H:%M:%S ') + s + '\n'); lf.flush()
    runs = {}                                  # path -> number of runs (this process)
    t_end = time.time() + hours * 3600; nrun = 0
    log('start shard', shard, 'hours', hours, 'slice', slc, 'starts', len(starts), 'code', code_version())
    while time.time() < t_end - 5:
        pool = [str(f) for f in sorted((out / 'pool').glob('*.bfx'))] + [str(f) for f in sorted((out / 'found').glob('*.bfx'))]
        cands = []
        for f in starts + pool:
            try:
                A = int(Path(f).name.split('-a')[1].split('-')[0]) if '-a' in Path(f).name else None
            except Exception:
                A = None
            cands.append((A, f))
        known = {}
        def A_of(f):
            if f not in known: known[f] = metrics(load(f))[0]
            return known[f]
        cands = [(A if A is not None else A_of(f), f) for A, f in cands]
        cands = [x for x in cands if x[0] <= 54]
        if not cands: log('no starts'); break
        amin = min(x[0] for x in cands)
        if rng.random() < 0.7:
            sub = [f for A, f in cands if A == amin]
            lo = min(runs.get(f, 0) for f in sub)
            f = rng.choice([x for x in sub if runs.get(x, 0) == lo])
        else:
            f = rng.choice(cands)[1]
        runs[f] = runs.get(f, 0) + 1
        c = load(f); m0 = metrics(c)
        plus, psplit, horizon, redec, pmerge = rng.choice(PARAMS)
        seed = rng.randrange(1, 1 << 30); nrun += 1
        secs = min(slc, max(5.0, t_end - time.time() - 3))
        tag = 'r%d-%05d' % (shard, nrun)
        wd = out / 'work' / tag
        t0 = time.time()
        try:
            cap = m0[1] if rng.random() < adcap_prob else 0
            res, wlog = W.run(c, wd, secs, seed, plus, psplit, horizon, redec, tag, cap, 12, 0, 0.0, pmerge)
        except Exception as e:
            log('run error', tag, repr(e)); continue
        spans = [ln for ln in wlog.splitlines() if ln.startswith('spans')]
        rec = {'run': tag, 'start': f, 'start_metrics': m0, 'plus': plus, 'psplit': psplit, 'horizon': horizon, 'redec': redec, 'pmerge': pmerge,
               'seed': seed, 'adcap': cap, 'seconds': round(time.time() - t0, 1), 'results': [], 'spans': spans[-1] if spans else None, 'new_pool': 0}
        bestA = m0[0]
        for nc, A in res:
            m = metrics(nc)
            if m[0] >= m0[0]: continue
            if m[0] >= amin:          # lower than its start, but not below the campaign's lowest AND count: log only
                rec['results'].append(m); log('REACHED', m, 'from', Path(f).name, m0); continue
            name = 'aes-sbox-a%d-ad%d-g%d-gd%d-x1w-%s' % (m + (tag,))
            bp = out / 'found' / (name + '.bfx'); bp.write_text(core.to_kernel(nc))
            r = aes_check.check(str(bp))
            if not r['ok']:
                bp.rename(out / 'found' / (name + '.FAILED')); log('CHECK FAILED', name); continue
            nc.name = name
            (out / 'found' / (name + '.circ.txt')).write_text(core.write_ncff(nc, MODEL, comments=['agent X1 flip/split walk (bfw.c)']))
            (out / 'found' / (name + '.json')).write_text(json.dumps({'method': 'x1 walkcamp: bfw flip/split walk + x1lib.materialise',
                'start': f, 'start_metrics': m0, 'plus': plus, 'psplit': psplit, 'horizon': horizon, 'redec': redec, 'pmerge': pmerge, 'seed': seed,
                'slice_s': secs, 'metrics': m, 'aes_check_ok': True, 'new_point_vs_published': bool(r.get('new_point')),
                'code_version': code_version(), 'time': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}, indent=1))
            rec['results'].append(m); bestA = min(bestA, m[0])
            log('TARGET' if m[0] <= target else 'LOWER', name, 'from', Path(f).name, m0)
        # same-A circuits with new spans (dumped by bfw for its best A) -> pool
        for pf in sorted(wd.glob('%s-s%d.span*.prog' % (tag, seed))):
            A = int(pf.name.split('.A')[1].split('.')[0])
            if A > bestA or rec['new_pool'] >= 12: continue
            q = W.read_prog(pf, c.n, c.m)
            if not X.check(q, W.TARGET): continue
            nc = X.materialise(q, random.Random(seed))
            if tuple(nc.value_table()) != sbox(): continue
            m = metrics(nc)
            if m[0] != A or A > min(amin, bestA): continue      # only the campaign's lowest AND count goes to the pool
            h = hashlib.sha1(core.to_kernel(nc).encode()).hexdigest()[:10]
            (out / 'pool' / ('pool-a%d-ad%d-g%d-gd%d-%s.bfx' % (m + (h,)))).write_text(core.to_kernel(nc))
            rec['new_pool'] += 1
        with open(out / ('runs-%d.jsonl' % shard), 'a') as rf: rf.write(json.dumps(rec) + '\n')
        log(tag, Path(f).name[:50], m0, 'params', (plus, psplit, horizon, redec, pmerge), '->', rec['results'], rec['spans'], 'pool+%d' % rec['new_pool'])
        # keep the work directory small
        for pf in wd.glob('*'):
            if pf.suffix in ('.prog',) or pf.name.startswith('bfw-'): pf.unlink()
    log('end shard', shard, 'runs', nrun)


if __name__ == '__main__':
    main()
