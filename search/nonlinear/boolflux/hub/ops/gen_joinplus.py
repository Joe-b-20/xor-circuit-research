#!/usr/bin/env python3
"""Hub generator gen_joinplus: hybrid AND structures by join+ (hub/joinplus.py), then polish.

    python3 hub/ops/gen_joinplus.py --archive DIR --in ID --seed S --seconds T --out JOBDIR

join+ joins the input with archive partners in both roles where the plain join fails because some
cut functions are outside the front's span: the partner's missing products (<= 6) are added to the
front.  This crosses families (e.g. A28/A29 backs on BP fronts give A30-A31 hybrids).  The raw hybrids
carry 20-60 extra XORs, so the cheapest few (lowest A, then G) are polished with the gate kernel
(caps A, AD of the hybrid, no GD cap) and every result the archive would place is a candidate.
First 40 % of T: enumeration over random partners; rest: polishes.
"""
import sys
import time
from pathlib import Path

OPS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(OPS_DIR.parents[1].parent))
from boolflux.hub.archive import GEN_SLACK  # noqa: E402
from boolflux.hub import ops as HO                       # noqa: E402
from boolflux.hub.common import core, metrics, sbox      # noqa: E402
from boolflux.hub import join as J, joinplus as JP      # noqa: E402


def op_gen_joinplus(ar, args, rng, out):
    X = J.Prepared(ar.circuit(args.inp), args.inp)
    pool = [ids[0] for ids in ar.cells.values() if ids and ids[0] != args.inp]
    rng.shuffle(pool)
    t0 = time.time(); raw = {}; tried = 0
    for pid in pool:
        if time.time() - t0 > 0.4 * args.seconds: break
        P = J.Prepared(ar.circuit(pid), pid)
        for F, B in ((X, P), (P, X)):
            for c, LX, LY, nint, nadd in JP.joinplus_all(F, B, max_add=6):
                tried += 1
                m = metrics(c)
                if m not in raw or len(c.gates) < len(raw[m][0].gates):
                    raw[m] = (c, {'front': F.id, 'back': B.id, 'LX': LX, 'LY': LY, 'interface_gates': nint, 'added_ands': nadd})
    order = sorted(raw.items(), key=lambda kv: (-ar.gain(kv[0]), kv[0][0], kv[0][2]))
    cands = {}; polished = []
    left = args.seconds - (time.time() - t0)
    npol = min(3, len(order))
    for k, (m, (c, d)) in enumerate(order[:npol]):
        secs = max(5.0, left / npol - 1)
        kd = out / ('p%d' % k); kd.mkdir(exist_ok=True)
        if ar.would_place(m, GEN_SLACK): cands[core.to_kernel(c)] = (c, d)
        pc, info = HO._kernel(c, {'A': m[0], 'AD': m[1], 'GD': None}, args.objective, rng.randrange(1 << 30), secs, kd, args.archive)
        for x in pc:
            if tuple(x.value_table()) != sbox(): continue
            mx = metrics(x); polished.append((m, mx))
            if ar.would_place(mx, GEN_SLACK): cands[core.to_kernel(x)] = (x, dict(d, polished_from=m))
    cl = sorted(cands.values(), key=lambda cd: (-ar.gain(metrics(cd[0])), metrics(cd[0])))[:args.max_cands]
    return [c for c, d in cl], {'tried': tried, 'raw': len(raw), 'polished': polished, 'joins': [d for c, d in cl]}


HO.OPS['gen_joinplus'] = op_gen_joinplus

if __name__ == '__main__':
    sys.exit(HO.main('gen_joinplus'))
