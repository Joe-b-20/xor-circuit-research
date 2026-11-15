#!/usr/bin/env python3
"""Kernel polish of one circuit under caps (hub kernel settings):
    python3 polish_one.py FILE OUT_DIR SECONDS SEED [A,AD,GD caps; '-' = none] [--rebuild]
--rebuild: first forget the XOR network (x1lib.extract + materialise), to measure how well the kernel
recovers a good linear layer from the naive one.  Prints start and result metrics."""
import sys, random
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import x1lib as X
from boolflux.hub import ops as HO
from boolflux.hub.common import load, metrics, sbox, core

f, out, secs, seed = sys.argv[1], Path(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4])
out.mkdir(parents=True, exist_ok=True)
c = load(f); m0 = metrics(c)
if '--rebuild' in sys.argv:
    c = X.materialise(X.extract(c), random.Random(seed))
m1 = metrics(c)
caps = {'A': m1[0], 'AD': m1[1], 'GD': None}
if len(sys.argv) > 5 and not sys.argv[5].startswith('--'):
    a, ad, gd = (None if x in ('', '-') else int(x) for x in sys.argv[5].split(','))
    caps = {'A': a, 'AD': ad, 'GD': gd}
cs, info = HO._kernel(c, caps, HO.DEFAULT_OBJECTIVE, seed, secs, out, out)
for pc in cs:
    ok = tuple(pc.value_table()) == sbox()
    m = metrics(pc)
    name = 'pol-a%d-ad%d-g%d-gd%d-s%d.bfx' % (m + (seed,))
    if ok: (out / name).write_text(core.to_kernel(pc))
    print(Path(f).name[:50], 'orig', m0, 'start', m1, 'caps', caps, '->', m, 'ok', ok, 't_imp', info.get('t_last_improvement'), flush=True)
