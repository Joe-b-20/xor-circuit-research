#!/usr/bin/env python3
"""Hub generator gen_skel: new AND structures by skeleton moves, for joins and linear operators.

    python3 hub/ops/gen_skel.py --archive DIR --in ID --seed S --seconds T --out JOBDIR

Loop until T: extract the AND skeleton of the input (products of affine forms over inputs and earlier
products), apply 1-3 accepted skeleton moves (the skeleton kernel kernel/skel.c with cap.k = the
input's AND count and max_acc = 1-3: swap a leaf product for another product congruent modulo the
span of the rest, merge two leaves, split, perturb), rebuild the XOR logic seeded with the input (its
gates are kept wherever their function survives), then a short gate-kernel polish (8 s, caps A =
input A, AD = input AD, no GD cap).  Every rebuilt-and-polished circuit the archive would place (new
cell, lower G in its cell, or within the near-front slack) is a candidate: a different product set
with near-front cost, i.e. a new partner for join and a new start for polish/pull/trb.  Measured
before this generator existed: a single move costs +0..+19 gates (BP-family circuits) and +12..+42
(28-AND circuits) after the seeded rebuild.
"""
import hashlib
import subprocess
import sys
import time
from pathlib import Path

OPS_DIR = Path(__file__).resolve().parent
PKG = OPS_DIR.parents[1]                                 # search/nonlinear/boolflux
sys.path.insert(0, str(PKG.parent))                      # search/nonlinear/
from boolflux.hub.archive import GEN_SLACK  # noqa: E402
from boolflux.hub import ops as HO                       # noqa: E402
from boolflux.hub.common import core, metrics, sbox, MODEL   # noqa: E402
from boolflux import skeleton                            # noqa: E402

SKEL = {'w.a': 1, 'w.lin': 0.02, 'T0': 0.3, 'Tperiod_it': 4000, 'mv.swap': 4, 'mv.merge': 3,
        'mv.split': 1, 'mv.perturb': 1, 'pairs': 60000, 'fext': 400, 'emit_current': 1}


def skel_bin(archive_dir):
    src = PKG / 'kernel' / 'skel.c'
    h = hashlib.sha1(src.read_bytes()).hexdigest()[:10]
    b = Path(archive_dir) / 'bin' / ('skel-' + h)
    if not b.exists():
        b.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['gcc', '-O3', '-march=native', '-o', str(b) + '.tmp', str(src), '-lm'], check=True)
        Path(str(b) + '.tmp').rename(b)
    return b


def kick(c, out, seed, nacc, archive_dir):
    sk = skeleton.extract(c)
    outs = core.tables_from_values(c.n, c.m, list(sbox()))
    sp = out / 'k.skin'; so = out / 'k.skout'; cp = out / 'k.skcfg'
    sp.write_text(skeleton.write_skel(sk, outs))
    A = sum(1 for g in c.gates if g[0] in core.NONLINEAR_OPS)
    cfg = dict(SKEL); cfg.update({'in': sp, 'out': so, 'seed': seed, 'iters': 20000, 'seconds': 10, 'max_acc': nacc, 'cap.k': A})
    cp.write_text(''.join('%s %s\n' % kv for kv in cfg.items()))
    r = subprocess.run([str(skel_bin(archive_dir)), str(cp)], capture_output=True, text=True)
    if r.returncode != 0 or not so.exists(): return None
    sk2 = skeleton.read_skel(so.read_text())
    if sk2['ands'] == sk['ands']: return None
    c2 = skeleton.synthesize(sk2, MODEL.ops(), name='kick', parent=c)
    return c2 if tuple(c2.value_table()) == sbox() else None


def op_gen_skel(ar, args, rng, out):
    c = ar.circuit(args.inp); A, AD, G, GD = metrics(c)
    t0 = time.time(); cands = {}; tried = []; k = 0
    while time.time() - t0 < args.seconds - 9:
        k += 1
        kd = out / ('k%02d' % k); kd.mkdir(exist_ok=True)
        nacc = rng.choice([1, 1, 2, 3])
        kc = kick(c, kd, rng.randrange(1 << 30), nacc, args.archive)
        if kc is None: tried.append((nacc, None)); continue
        km = metrics(kc)
        pc, info = HO._kernel(kc, {'A': A, 'AD': AD, 'GD': None}, args.objective, rng.randrange(1 << 30), 8.0, kd, args.archive)
        best = None
        for x in [kc] + pc:
            if tuple(x.value_table()) != sbox(): continue
            m = metrics(x)
            if ar.would_place(m, GEN_SLACK) and (best is None or m < metrics(best)): best = x
        tried.append((nacc, km, metrics(pc[0]) if pc else None))
        if best is not None: cands[core.to_kernel(best)] = best
    cl = sorted(cands.values(), key=lambda x: (-ar.gain(metrics(x)), metrics(x)))
    return cl[:args.max_cands], {'kicks': k, 'tried': tried[:40]}


HO.OPS['gen_skel'] = op_gen_skel

if __name__ == '__main__':
    sys.exit(HO.main('gen_skel'))
