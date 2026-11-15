#!/usr/bin/env python3
"""Exhaustive A-reduction scan over level-1 windows (agent R2).

    python3 scan_l1.py OUT.jsonl LEVEL FILE_OR_ARCHIVE_ID ...   (args: .bfx/.circ.txt paths or ARCHIVE_DIR:ID)

For every subset S (|S| >= 2) of the ANDs at AND level LEVEL (default 1) of each circuit: window with
full downstream linear closure D and wide slack C (every signal independent of S with AND level <=
LEVEL), r = dim R.  If r < k: search for m = r products (operands affine over signals of AND level
<= LEVEL-1; exhaustive over all non-constant affine operands a when dim span(O) <= 12, every b by
elimination).  When r = k - 1, m = r is the only A-reducing size, so 'no spanning set' is a complete
negative for that window (within the window model: fixed S, full D, these targets, this C).
One JSON line per circuit with counts, plus lines for every r < k window."""
import itertools, json, random, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(next(q for q in HERE.parents if (q / 'boolflux' / 'core.py').exists())))
from boolflux import core                      # noqa: E402
from boolflux.hub.common import metrics, load   # noqa: E402
import aslack as AS                            # noqa: E402

out = open(sys.argv[1], 'a'); LEV = int(sys.argv[2])
rng = random.Random(1)
for spec in sys.argv[3:]:
    if ':' in spec and not Path(spec).exists():
        d, i = spec.rsplit(':', 1); c = core.from_kernel((Path(d) / 'archive' / (i + '.bfx')).read_text(), i)
    else:
        c = load(spec)
    t0 = time.time(); I = AS.Info(c); ands = I.bylevel.get(LEV, [])
    cnt = {'windows': 0, 'r_lt_k': 0, 'r_eq_k_minus_1': 0, 'spanned': 0, 'exhaustive': 0, 'nonexh': 0}
    for k in range(2, len(ands) + 1):
        for S in itertools.combinations(ands, k):
            W = AS.Window(I, list(S), 'wide', rng, ddepth=None)
            cnt['windows'] += 1
            if W.r >= k: continue
            cnt['r_lt_k'] += 1; cnt['r_eq_k_minus_1'] += (W.r == k - 1)
            prods = W.products(rng, exhaustive_dim=12)
            ex = getattr(W, 'exhaustive', False); cnt['exhaustive' if ex else 'nonexh'] += 1
            ch = W.pick(prods, rng) if prods else None
            row = {'circ': spec, 'S': list(S), 'k': k, 'r': W.r, 'dimV': W.dimV, 'dimO': getattr(W, 'dimO', None),
                   'exhaustive': ex, 'nprods': len(prods), 'spanned': ch is not None, 'targets': len(W.targets)}
            if ch is not None:
                cnt['spanned'] += 1
                rows = W.target_rows(ch, rng)
                nc = AS.rebuild(W, ch, rows, rng) if rows else None
                if nc is not None:
                    row['func_ok'] = tuple(nc.value_table()) == tuple(c.value_table()); row['m1'] = metrics(nc)
                    Path(sys.argv[1]).with_suffix('').mkdir(exist_ok=True)
                    (Path(sys.argv[1]).with_suffix('') / ('%s-%s.bfx' % (Path(spec).stem.replace(':', '_'), '-'.join(map(str, S))))).write_text(core.to_kernel(nc))
            out.write(json.dumps(row) + '\n'); out.flush()
    out.write(json.dumps({'circ': spec, 'm': metrics(c), 'level': LEV, 'ands_at_level': len(ands), 'counts': cnt,
                          'secs': round(time.time() - t0, 1)}) + '\n'); out.flush()
