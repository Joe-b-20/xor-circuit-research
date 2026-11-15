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

from .common import core, metrics, code_version, cid, HUB, PKG
from .. import objective as OBJ
from .archive import Archive
from . import join as J

KDEFAULTS = {'T0': 0.6, 'Tperiod_it': 20000, 'stall_it': 60000, 'uphill': 1.0, 'max_excess': 8,
             'mv.resub1': 1, 'mv.resub2': 2, 'mv.resub3': 1, 'dmax': 220, 'pdiv': 90,
             'nl_samples': 12, 'cand_cap': 40, 'fraig': 1}
KEYW = OBJ.WKEY
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
    cfg.update(OBJ.weights(objective))      # the package's own key validation, weights and `lex` (one definition)
    for op in (8, 6, 9, 3): cfg['cost.%d' % op] = 1
    for k, key in (('A', 'cap.a'), ('AD', 'cap.ad'), ('GD', 'cap.gd')):
        if caps.get(k) is not None: cfg[key] = caps[k]
    cfg.update({'in': sp, 'out': bp, 'seed': seed, 'seconds': seconds})
    cp.write_text(''.join('%s %s\n' % kv for kv in cfg.items()))
    kb = kernel_bin(archive_dir)
    with open(out / 'kernel.log', 'w') as lf:
        try:
            rc = subprocess.run([str(kb), str(cp)], stdout=lf, stderr=subprocess.STDOUT,
                                timeout=float(seconds) * 1.5 + 30).returncode
        except subprocess.TimeoutExpired:
            rc = 'timeout'
    if rc != 0:      # a kernel that dies (bad config key, internal check, signal) is a failed job, not "no candidate"
        raise OpError('kernel %s exit %s: %s' % (kb.name, rc, (out / 'kernel.log').read_text()[-300:].strip()))
    t_imp = None
    for ln in (out / 'kernel.log').read_text().splitlines():
        if ln.startswith('best t '): t_imp = float(ln.split()[2])
    cands = []
    if bp.exists():
        cands.append(core.from_kernel(bp.read_text(), 'best'))
    # kernel binary name = bfx-<sha1(kernel/bfx.c)[:10]>: 40cd99d184 = 417e449, 945fb150c6 = f8a26e3 (review 4)
    return cands, {'kernel_settings': cfg, 't_last_improvement': t_imp, 'kernel_bin': kb.name}


class OpError(Exception):
    pass


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
    if which == 'GD': caps['GD'] = max(1, GD - rng.choice([1, 1, 2, 3])); caps['AD'] = None
    elif which == 'AD': caps['AD'] = max(1, AD - 1)
    else: caps['A'] = max(1, A - 1)
    cands, info = _kernel(c, caps, args.objective, args.seed, args.seconds, out, args.archive)
    info.update({'caps': caps, 'lowered': which})
    return cands, info


def join_partners(ar, inp, since, rng, limit=None):
    """Partner ids for a join of `inp`.
    since is None (legacy, until 2026-11-14): front ids first, then the first member of the other
      cells in random order, cut at `limit`.  With a front of ~300 ids this was the front only,
      identical in every job, and non-front circuits (generator / nursery structures) never joined.
    since = t: every cell member (front or not, all K structures) admitted after t, oldest first,
      so that a pass that runs out of time can be continued from the last partner done."""
    if since is None:
        front = [i for i in ar.front_ids() if i != inp]
        others = [ids[0] for ids in ar.cells.values() if ids and ids[0] != inp and ids[0] not in front]
        rng.shuffle(others)
        return (front + others)[:limit]
    ids = [i for members in ar.cells.values() for i in members if i != inp and ar.rec[i]['t_admit'] > since]
    return sorted(ids, key=lambda i: (ar.rec[i]['t_admit'], i))


def op_join(ar, args, rng, out):
    """the input against archive partners in both roles (join_partners); keeps candidates that the
    archive would place (lower or tie G in their cell).  info['joined_through']: every partner
    admitted up to this time has been joined with the input (the scheduler passes it back as
    --since, so no (target, partner) pair is computed twice by this target's jobs)."""
    X = J.Prepared(ar.circuit(args.inp), args.inp)
    t_load = max((r['t_admit'] for r in ar.rec.values()), default=0.0)
    partners = join_partners(ar, args.inp, args.since, rng, args.partners)
    t0 = time.time(); tried = 0; kept = []; done = 0; through = args.since
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
        done += 1
        if args.since is not None: through = ar.rec[pid]['t_admit']
    if args.since is not None and done == len(partners): through = max(t_load, args.since)
    kept.sort(key=lambda x: -x[0])
    dropped = max(0, len(kept) - args.max_cands)
    kept = kept[:args.max_cands]
    return [c for g, c, d in kept], {'partners': len(partners), 'partners_done': done, 'tried': tried, 'kept_over_limit': dropped,
                                    'since': args.since, 'joined_through': through, 'joins': [d for g, c, d in kept]}


def op_trb(ar, args, rng, out):
    from . import trb_impl
    c = ar.circuit(args.inp); A, AD, G, GD = metrics(c)
    t0 = time.time(); best = {}; reps = 0; errors = {}
    while time.time() - t0 < args.seconds:
        D = GD - rng.choice([0, 0, 1])
        kind = rng.choice(['bottom', 'top', 'mid', 'random', 'random'])
        try:
            nc, info = trb_impl.rebuild(c, D, kind, rng)
        except Exception as e:
            k = type(e).__name__; errors[k] = errors.get(k, 0) + 1
            continue
        reps += 1
        m = metrics(nc)
        if nc is c or not ar.would_place(m): continue
        best[core.to_kernel(nc)] = nc
        if rng.random() < 0.5: c = nc          # chain rebuilds sometimes
    return list(best.values())[:args.max_cands], {'reps': reps, 'rebuild_errors': errors}


OPS = {'polish': op_polish, 'pull': op_pull, 'join': op_join, 'trb': op_trb}


def parse_caps(text):
    """'A,AD,GD' with '' or '-' for no cap -> {'A': .., 'AD': .., 'GD': ..}"""
    parts = text.split(',')
    if len(parts) != 3: raise SystemExit('--caps wants A,AD,GD (use - for no cap), got %r' % text)
    try:
        a, ad, gd = (None if x.strip() in ('', '-') else int(x) for x in parts)
    except ValueError:
        raise SystemExit('--caps wants integers or -, got %r' % text)
    if any(v is not None and v < 1 for v in (a, ad, gd)): raise SystemExit('--caps values must be positive')
    return {'A': a, 'AD': ad, 'GD': gd}


def main(name, argv=None):
    """Exit code 0: record.json written, candidates listed in it.  Exit code 1: the operator failed;
    record.json still written, with 'error' (and the traceback in the job log).  Exit code 2: bad
    command line (no record)."""
    ap = argparse.ArgumentParser(prog='op_' + name)
    ap.add_argument('--archive', required=True); ap.add_argument('--in', dest='inp', required=True)
    ap.add_argument('--in2'); ap.add_argument('--caps')
    ap.add_argument('--objective', default=DEFAULT_OBJECTIVE)
    ap.add_argument('--seed', type=int, default=1); ap.add_argument('--seconds', type=float, default=60)
    ap.add_argument('--partners', type=int, default=300, help='join without --since: partner limit (legacy pool)')
    ap.add_argument('--since', type=float, default=None,
                    help='join: partners = every cell member admitted after this time (0 = all); omit for the legacy pool')
    ap.add_argument('--max-cands', type=int, default=40)
    ap.add_argument('--out', required=True)
    args = ap.parse_args(argv)
    if args.caps: args.caps = parse_caps(args.caps)
    OBJ.parse(args.objective)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    if any(out.glob('cand-*.bfx')): raise SystemExit('--out %s already holds candidates: a job directory is used once' % out)
    rng = random.Random(args.seed)
    t0 = time.time(); r0 = resource.getrusage(resource.RUSAGE_SELF); c0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    cands, info, error = [], {}, None
    try:
        ar = Archive(args.archive)
        if args.inp not in ar.rec: raise OpError('--in %s is not in the archive' % args.inp)
        if args.in2 and args.in2 not in ar.rec: raise OpError('--in2 %s is not in the archive' % args.in2)
        cands, info = OPS[name](ar, args, rng, out)
    except Exception as e:
        import traceback
        traceback.print_exc(); error = '%s: %s' % (type(e).__name__, e); cands = []
    ids = []
    for k, c in enumerate(cands):
        (out / ('cand-%03d.bfx' % k)).write_text(core.to_kernel(c)); ids.append(cid(c))
    r1 = resource.getrusage(resource.RUSAGE_SELF); c1 = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu = (r1.ru_utime + r1.ru_stime - r0.ru_utime - r0.ru_stime) + (c1.ru_utime + c1.ru_stime - c0.ru_utime - c0.ru_stime)
    rec = {'operator': name, 'inputs': [args.inp] + ([args.in2] if args.in2 else []), 'caps': args.caps,
           'objective': args.objective, 'seed': args.seed, 'seconds': args.seconds, 'wall_s': round(time.time() - t0, 2),
           'cpu_s': round(cpu, 2), 'candidates': len(cands), 'cand_ids': ids, 'code_version': code_version(), 'info': info}
    if error: rec['error'] = error
    (out / 'record.json').write_text(json.dumps(rec, indent=1, default=str))
    return 1 if error else 0
