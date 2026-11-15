#!/usr/bin/env python3
"""Per-job improvement rate of aslack on fixed targets under their own caps (agent R2).

    python3 fixed_test.py ARCHIVE_CAMPAIGN OUTDIR JOBS SECONDS SEED A/AD/G/GD ...

For each tuple: the archive's cell minimum with those metrics; JOBS independent aslack jobs (seeds
differ) under caps = its own (A, AD, GD), objective a,ad,cost,gd.  A job 'improves' if some candidate
has viol 0 and (A, AD, G, GD) lexicographically smaller than the input.  Improvements are checked with
aes_check and saved to OUTDIR/found/ (+ JSON sidecar).  One JSON line per job in OUTDIR/fixed.jsonl."""
import argparse, hashlib, json, random, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
PKG_PARENT = next(q for q in HERE.parents if (q / 'boolflux' / 'core.py').exists())
sys.path.insert(0, str(PKG_PARENT)); sys.path.insert(0, str(PKG_PARENT / 'boolflux' / 'campaigns'))
from boolflux import core                         # noqa: E402
from boolflux.hub.archive import Archive          # noqa: E402
from boolflux.hub.common import metrics           # noqa: E402
import op_aslack as OP                            # noqa: E402
import aes_check                                  # noqa: E402

camp, outd, J, secs, seed = sys.argv[1], Path(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5])
tuples = [tuple(int(x) for x in t.split('/')) for t in sys.argv[6:]]
outd.mkdir(parents=True, exist_ok=True); (outd / 'found').mkdir(exist_ok=True); (outd / 'jobs').mkdir(exist_ok=True)
md5 = {f: hashlib.md5((HERE / f).read_bytes()).hexdigest() for f in ('aslack.py', 'op_aslack.py', 'fixed_test.py')}
ar = Archive(camp); rng = random.Random(seed)


class FakeAr:
    def __init__(self, c): self.c = c
    def circuit(self, i): return self.c
    def would_place(self, m): return True
    def gain(self, m): return 0.0


log = open(outd / 'fixed.jsonl', 'a')
for t in tuples:
    k = (t[0], t[1], t[3]); ids = ar.cells.get(k) or []
    ids = [i for i in ids if ar.rec[i]['G'] == t[2]]
    if not ids:
        log.write(json.dumps({'tuple': t, 'error': 'no cell minimum with these metrics'}) + '\n'); continue
    cid = ids[0]; c = ar.circuit(cid); m0 = metrics(c)
    for j in range(J):
        jd = outd / 'jobs' / ('%s-%d' % ('_'.join(map(str, t)), j)); jd.mkdir(exist_ok=True)
        a = argparse.Namespace(inp=cid, caps={'A': m0[0], 'AD': m0[1], 'GD': m0[3]}, objective='a,ad,cost,gd',
                               seed=rng.randrange(1, 1 << 30), seconds=secs, archive=str(outd), max_cands=40, npolish=3,
                               hunt=0.15, ztries=4, partners=0, in2=None)
        t0 = time.time()
        cands, info = OP.op_aslack(FakeAr(c), a, random.Random(a.seed), jd)
        ms = sorted(metrics(x) for x in cands)
        feas = [(m, x) for m, x in zip([metrics(x) for x in cands], cands) if m[0] <= m0[0] and m[1] <= m0[1] and m[3] <= m0[3]]
        better = sorted([(m, x) for m, x in feas if m < m0], key=lambda v: v[0])
        tie_new = sum(1 for m, x in feas if m == m0 and core.to_kernel(x) != core.to_kernel(c))
        row = {'tuple': t, 'id': cid, 'job': j, 'seed': a.seed, 'secs': round(time.time() - t0, 1), 'improved': bool(better),
               'best': better[0][0] if better else (min(m for m, x in feas) if feas else None), 'feasible_cands': len(feas),
               'ties_new_structure': tie_new, 'stats': {kk: info['stats'].get(kk) for kk in ('windows', 'func_ok', 'new_products', 'a_red', 'r_lt_k')}}
        if better:
            m, x = better[0]; kt = core.to_kernel(x)
            name = 'R2-fixed-a%d-ad%d-g%d-gd%d-%s' % (*m, hashlib.sha1(kt.encode()).hexdigest()[:8])
            p = outd / 'found' / (name + '.bfx'); p.write_text(kt)
            r = aes_check.check(str(p))
            row['file'] = str(p); row['aes_check_ok'] = r.get('ok'); row['new_point'] = r.get('new_point')
            (outd / 'found' / (name + '.json')).write_text(json.dumps({'from': cid, 'from_metrics': m0, 'metrics': m, 'seed': a.seed,
                'op': 'aslack fixed_test', 'code_md5': md5, 'time_utc': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
                'aes_check_ok': r.get('ok'), 'new_point': r.get('new_point')}, indent=1, default=str))
        log.write(json.dumps(row, default=str) + '\n'); log.flush()
