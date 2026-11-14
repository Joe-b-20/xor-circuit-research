"""Hub operators.  Common CLI (op_<name>.py):

    op_<name>.py --archive DIR --in ID [--in2 ID] [--caps A,AD,GD] [--objective KEYS] --seed S --seconds T --out JOBDIR

Each writes candidate circuits JOBDIR/cand-*.bfx and JOBDIR/record.json (operator, inputs, settings,
seed, timing, candidate count, code version).  Operators never admit; the scheduler verifies and admits.
  polish  gate kernel (bfx, strict lexicographic objective) under the given caps (default: the input's own)
  pull    the same with one cap lowered (GD by 1-3, AD by 1 or A by 1; repair mode of the kernel)
  join    transplants of the input with archive partners in both roles (join.py)
  trb     timing-aware XOR-region rebuilds (trb_impl.py, copy of strategies/F/trb.py)
"""
from __future__ import annotations

import argparse
import json
import random
import resource
import subprocess
import time
from pathlib import Path

from .common import core, metrics, code_version, HUB, PKG
from .archive import Archive
from . import join as J

KDEFAULTS = {'T0': 0.6, 'Tperiod_it': 20000, 'stall_it': 60000, 'uphill': 1.0, 'max_excess': 8,
             'mv.resub1': 1, 'mv.resub2': 2, 'mv.resub3': 1, 'dmax': 220, 'pdiv': 90,
             'nl_samples': 12, 'cand_cap': 40, 'fraig': 1}
KEYW = {'cost': 'w.cost', 'g': 'w.g', 'a': 'w.a', 'gd': 'w.gd', 'ad': 'w.ad'}
DEFAULT_OBJECTIVE = 'a,ad,cost,gd'        # research priorities: AND count, AND depth, then G, GD


def kernel_bin(archive_dir):
    """private kernel binary built from kernel/bfx.c into ARCHIVE_DIR/bin (once per source version)"""
    import hashlib
    src = PKG / 'kernel' / 'bfx.c'
    h = hashlib.sha1(src.read_bytes()).hexdigest()[:10]
    b = Path(archive_dir) / 'bin' / ('bfx-' + h)
    if not b.exists():
        b.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['gcc', '-O3', '-march=native', '-o', str(b) + '.tmp', str(src), '-lm'], check=True)
        Path(str(b) + '.tmp').rename(b)
    return b


def _kernel(c, caps, objective, seed, seconds, out, archive_dir):
    sp = out / 'start.bfx'; sp.write_text(core.to_kernel(c))
    bp = out / 'best.bfx'; cp = out / 'kernel.cfg'
    cfg = dict(KDEFAULTS)
    keys = [k.strip() for k in objective.split(',')]
    for k in KEYW.values(): cfg[k] = 0.0
    for i, k in enumerate(keys): cfg[KEYW[k]] = cfg.get(KEYW[k], 0) + 10.0 ** (-4 * i)
    cfg['lex'] = ','.join(keys)
    for op in (8, 6, 9, 3): cfg['cost.%d' % op] = 1
    for k, key in (('A', 'cap.a'), ('AD', 'cap.ad'), ('GD', 'cap.gd')):
        if caps.get(k) is not None: cfg[key] = caps[k]
    cfg.update({'in': sp, 'out': bp, 'seed': seed, 'seconds': seconds})
    cp.write_text(''.join('%s %s\n' % kv for kv in cfg.items()))
    kb = kernel_bin(archive_dir)
    with open(out / 'kernel.log', 'w') as lf:
        subprocess.run([str(kb), str(cp)], stdout=lf, stderr=subprocess.STDOUT)
    t_imp = None
    for ln in (out / 'kernel.log').read_text().splitlines():
        if ln.startswith('best t '): t_imp = float(ln.split()[2])
    cands = []
    if bp.exists():
        cands.append(core.from_kernel(bp.read_text(), 'best'))
    # kernel binary name = bfx-<sha1(kernel/bfx.c)[:10]>: 40cd99d184 = 417e449, 945fb150c6 = f8a26e3 (review 4)
    return cands, {'kernel_settings': cfg, 't_last_improvement': t_imp, 'kernel_bin': kb.name}


def op_polish(ar, args, rng, out):
    c = ar.circuit(args.inp); A, AD, G, GD = metrics(c)
    caps = args.caps or {'A': A, 'AD': AD, 'GD': GD}
    cands, info = _kernel(c, caps, args.objective, args.seed, args.seconds, out, args.archive)
    info['caps'] = caps
    return cands, info


def op_pull(ar, args, rng, out):
    c = ar.circuit(args.inp); A, AD, G, GD = metrics(c)
    caps = dict(args.caps or {'A': A, 'AD': AD, 'GD': GD})
    which = rng.choice(['GD', 'GD', 'GD', 'AD', 'A'])
    if which == 'GD': caps['GD'] = GD - rng.choice([1, 1, 2, 3]); caps['AD'] = None
    elif which == 'AD': caps['AD'] = AD - 1
    else: caps['A'] = A - 1
    cands, info = _kernel(c, caps, args.objective, args.seed, args.seconds, out, args.archive)
    info.update({'caps': caps, 'lowered': which})
    return cands, info


def op_join(ar, args, rng, out):
    """the input against up to `partners` archive members (front first, then random cell minima), both roles;
    keeps candidates that the archive would place (lower or tie G in their cell)"""
    X = J.Prepared(ar.circuit(args.inp), args.inp)
    front = [i for i in ar.front_ids() if i != args.inp]
    others = [ids[0] for ids in ar.cells.values() if ids and ids[0] != args.inp and ids[0] not in front]
    rng.shuffle(others)
    partners = (front + others)[:args.partners]
    t0 = time.time(); tried = 0; kept = []
    seen = set()
    for pid in partners:
        if time.time() - t0 > args.seconds: break
        P = J.Prepared(ar.circuit(pid), pid)
        for F, B in ((X, P), (P, X)):
            for c, LX, LY, nint in J.join_all(F, B):
                tried += 1
                m = metrics(c)
                if not ar.would_place(m): continue
                k = core.to_kernel(c)
                if k in seen: continue
                seen.add(k)
                kept.append((ar.gain(m), c, {'front': F.id, 'back': B.id, 'LX': LX, 'LY': LY, 'interface_gates': nint}))
    kept.sort(key=lambda x: -x[0])
    kept = kept[:args.max_cands]
    return [c for g, c, d in kept], {'partners': len(partners), 'tried': tried, 'joins': [d for g, c, d in kept]}


def op_trb(ar, args, rng, out):
    from . import trb_impl
    c = ar.circuit(args.inp); A, AD, G, GD = metrics(c)
    t0 = time.time(); best = {}; reps = 0
    while time.time() - t0 < args.seconds:
        D = GD - rng.choice([0, 0, 1])
        kind = rng.choice(['bottom', 'top', 'mid', 'random', 'random'])
        try:
            nc, info = trb_impl.rebuild(c, D, kind, rng)
        except Exception:
            continue
        reps += 1
        m = metrics(nc)
        if nc is c or not ar.would_place(m): continue
        best[core.to_kernel(nc)] = nc
        if rng.random() < 0.5: c = nc          # chain rebuilds sometimes
    return list(best.values())[:args.max_cands], {'reps': reps}


OPS = {'polish': op_polish, 'pull': op_pull, 'join': op_join, 'trb': op_trb}


def main(name, argv=None):
    ap = argparse.ArgumentParser(prog='op_' + name)
    ap.add_argument('--archive', required=True); ap.add_argument('--in', dest='inp', required=True)
    ap.add_argument('--in2'); ap.add_argument('--caps')
    ap.add_argument('--objective', default=DEFAULT_OBJECTIVE)
    ap.add_argument('--seed', type=int, default=1); ap.add_argument('--seconds', type=float, default=60)
    ap.add_argument('--partners', type=int, default=300); ap.add_argument('--max-cands', type=int, default=40)
    ap.add_argument('--out', required=True)
    args = ap.parse_args(argv)
    if args.caps:
        a, ad, gd = (None if x in ('', '-') else int(x) for x in args.caps.split(','))
        args.caps = {'A': a, 'AD': ad, 'GD': gd}
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    t0 = time.time(); r0 = resource.getrusage(resource.RUSAGE_SELF); c0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    ar = Archive(args.archive)
    cands, info = OPS[name](ar, args, rng, out)
    for k, c in enumerate(cands):
        (out / ('cand-%03d.bfx' % k)).write_text(core.to_kernel(c))
    r1 = resource.getrusage(resource.RUSAGE_SELF); c1 = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu = (r1.ru_utime + r1.ru_stime - r0.ru_utime - r0.ru_stime) + (c1.ru_utime + c1.ru_stime - c0.ru_utime - c0.ru_stime)
    rec = {'operator': name, 'inputs': [args.inp] + ([args.in2] if args.in2 else []), 'caps': args.caps,
           'objective': args.objective, 'seed': args.seed, 'seconds': args.seconds, 'wall_s': round(time.time() - t0, 2),
           'cpu_s': round(cpu, 2), 'candidates': len(cands), 'code_version': code_version(), 'info': info}
    (out / 'record.json').write_text(json.dumps(rec, indent=1, default=str))
    return 0
