#!/usr/bin/env python3
"""AND-level lowering scan (agent R2): can a set S of ANDs at level L be replaced by ANDs at level L-1?

    python3 scan_depth.py OUT.jsonl MAXSUB SPEC ...     (SPEC: circuit file or ARCHIVE_DIR:ID)

For each circuit and each AND level L >= 2: every subset S of the level-L ANDs (all subsets when the
level has <= MAXSUB ANDs, else only the whole level and single ANDs).  Window: full downstream linear
closure D, wide slack C = signals independent of S with AND level <= L-1 (lower=1); new products with
operands affine over signals of AND level <= L-2, so they sit at level <= L-1; m = r products searched
(exhaustive over operands a when dim span(O) <= 12, i.e. L = 2; every b by elimination).  Spanned
windows are rebuilt and checked on 256 inputs; metrics recorded (AD drop = goal).  'Not spanned' with
exhaustive search is a [C] negative for that window model (m = r, products in V + R)."""
import itertools, json, random, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(next(q for q in HERE.parents if (q / 'boolflux' / 'core.py').exists())))
from boolflux import core                        # noqa: E402
from boolflux.hub.common import metrics, load, sbox   # noqa: E402
import aslack as AS                              # noqa: E402

outp = Path(sys.argv[1]); out = open(outp, 'a'); MAXSUB = int(sys.argv[2])
rng = random.Random(1)
fd = outp.with_suffix(''); fd.mkdir(exist_ok=True)
for spec in sys.argv[3:]:
    if ':' in spec and not Path(spec).exists():
        d, i = spec.rsplit(':', 1); c = core.from_kernel((Path(d) / 'archive' / (i + '.bfx')).read_text(), i)
    else:
        c = load(spec)
    t0 = time.time(); I = AS.Info(c); m0 = metrics(c)
    summ = {}
    for L in sorted(I.bylevel):
        if L < 2: continue
        ands = I.bylevel[L]
        if len(ands) <= MAXSUB:
            subsets = [S for k in range(1, len(ands) + 1) for S in itertools.combinations(ands, k)]
        else:
            subsets = [tuple(ands)] + [(a,) for a in ands]
        cnt = {'windows': 0, 'spanned': 0, 'exhaustive': 0, 'func_ok': 0, 'ad_drop': 0, 'a_drop': 0}
        for S in subsets:
            try:
                W = AS.Window(I, list(S), 'wide', rng, ddepth=None, lower=1)
                cnt['windows'] += 1
                prods = W.products(rng, exhaustive_dim=12, n_a=400)
                ex = getattr(W, 'exhaustive', False); cnt['exhaustive'] += ex
                ch = W.pick(prods, rng) if (prods or W.r == 0) else None
                if W.r == 0: ch = []
            except Exception as e:
                out.write(json.dumps({'circ': spec, 'L': L, 'S': list(S), 'error': repr(e)[:100]}) + '\n'); continue
            if ch is None: continue
            cnt['spanned'] += 1
            row = {'circ': spec, 'm0': m0, 'L': L, 'S': list(S), 'k': len(S), 'r': W.r, 'exhaustive': ex}
            rows = W.target_rows(ch, rng)
            nc = AS.rebuild(W, ch, rows, rng) if rows is not None else None
            if nc is not None and tuple(nc.value_table()) == sbox():
                cnt['func_ok'] += 1; m1 = metrics(nc); row['m1'] = m1
                cnt['ad_drop'] += m1[1] < m0[1]; cnt['a_drop'] += m1[0] < m0[0]
                if m1[1] < m0[1] or m1[0] < m0[0]:
                    (fd / ('%s-L%d-%s.bfx' % (Path(spec).name.replace(':', '_'), L, '-'.join(map(str, S))))).write_text(core.to_kernel(nc))
            out.write(json.dumps(row) + '\n'); out.flush()
        summ[L] = dict(cnt, ands=len(ands))
    out.write(json.dumps({'circ': spec, 'm': m0, 'summary': summ, 'secs': round(time.time() - t0, 1)}) + '\n'); out.flush()
