"""Hub operators.  Common CLI (op_<name>.py):

    op_<name>.py --archive DIR --in ID [--in2 ID] [--caps A,AD,GD] [--objective KEYS] --seed S --seconds T --out JOBDIR

Each writes candidate circuits JOBDIR/cand-*.bfx and JOBDIR/record.json (operator, inputs, settings,
seed, timing, candidate count, code version), and the run record JOBDIR/run.json + events.jsonl.gz
(runlog.py: command, git state, seeds, kernel, host; every kernel improvement and every candidate).
Operators never admit; the scheduler verifies and admits.  The function (aes-sbox or aes-invsbox)
is the process's ($BOOLFLUX_FUNCTION, set by the scheduler, or --function).
  polish  gate kernel (bfx, strict lexicographic objective) under the given caps (default: the input's own)
  pull    the same with one cap lowered (GD by 1-3, AD by 1 or A by 1; repair mode of the kernel)
  join    transplants of the input with archive partners in both roles (join.py)
  trb     timing-aware XOR-region rebuilds (trb_impl.py)
"""
from __future__ import annotations

import argparse
import json
import os
import random
import resource
import subprocess
import time
from pathlib import Path

from .common import aesfn, core, metrics, code_version, cid, HUB, PKG
from .. import objective as OBJ
from .. import runlog
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
        # Each builder writes to its own temporary name and renames atomically (with one shared `.tmp`
        # name, two builders could rename each other's half-written file).
        import tempfile
        b.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=b.name + '.', suffix='.tmp', dir=str(b.parent)); os.close(fd)
        try:
            subprocess.run(['gcc', '-O3', '-march=native', '-o', tmp, str(src), '-lm'], check=True)
            os.chmod(tmp, 0o755)
            os.replace(tmp, b)
        finally:
            if os.path.exists(tmp): os.unlink(tmp)
    return b


KERNEL_SRC = PKG / 'kernel' / 'bfx.c'


def kernel_record(b):
    """source and build command of a kernel_bin() binary, for run records (runlog.RunLog.add_kernel)"""
    return {'source': KERNEL_SRC, 'command': ['gcc', '-O3', '-march=native', '-o', str(b), str(KERNEL_SRC), '-lm']}


def _kernel(c, caps, objective, seed, seconds, out, archive_dir):
    sp = out / 'start.bfx'; sp.write_text(core.to_kernel(c))
    bp = out / 'best.bfx'; cp = out / 'kernel.cfg'
    cfg = dict(KDEFAULTS)
    cfg.update(OBJ.weights(objective))      # the package's own key validation, weights and `lex` (one definition)
    for op in (8, 6, 9, 3): cfg['cost.%d' % op] = 1
    for k, key in (('A', 'cap.a'), ('AD', 'cap.ad'), ('GD', 'cap.gd')):
        if caps.get(k) is not None: cfg[key] = caps[k]
    cfg.update({'in': sp, 'out': bp, 'seed': seed, 'seconds': seconds})
    kd = out / 'bests'; kd.mkdir(exist_ok=True)
    cfg['keep_bests'] = kd                 # instrumentation: every new best of the run (kernel writes best-<k>.bfx), not only the last
    cp.write_text(''.join('%s %s\n' % kv for kv in cfg.items()))
    kb = kernel_bin(archive_dir)
    if RUN is not None: RUN.add_kernel(kb, **kernel_record(kb))
    tk = time.monotonic()
    with open(out / 'kernel.log', 'w') as lf:
        try:
            rc = subprocess.run([str(kb), str(cp)], stdout=lf, stderr=subprocess.STDOUT,
                                timeout=float(seconds) * 1.5 + 30).returncode
        except subprocess.TimeoutExpired:
            rc = 'timeout'
    KTIME[0] += time.monotonic() - tk; KTIME[1] += 1
    if rc != 0:      # a kernel that dies (bad config key, internal check, signal) is a failed job, not "no candidate"
        raise OpError('kernel %s exit %s: %s' % (kb.name, rc, (out / 'kernel.log').read_text()[-300:].strip()))
    t_imp = None
    ktext = (out / 'kernel.log').read_text()
    ks = runlog.kernel_summary(ktext)            # stop reason, acceptance kinds, move counters (kstat lines)
    if RUN is not None:
        RUN.event('kernel-end', kernel_seed=seed, caps=caps, seconds=seconds, rc=rc, stats=ks)
    for ln in ktext.splitlines():
        if ln.startswith('best t '):
            t_imp = float(ln.split()[2])
            if RUN is not None:
                tk = ln.split(); d = {tk[i]: tk[i + 1] for i in range(1, len(tk) - 1, 2)}
                RUN.improvement({k: int(d[k]) for k in ('A', 'AD', 'G', 'GD') if k in d}, 'gate kernel',
                                t_kernel=float(d['t']), it=d.get('it'), move=d.get('mv'), kernel_seed=seed)
    cands = []
    if bp.exists():
        cands.append(core.from_kernel(bp.read_text(), 'best'))
    # kernel binary name = bfx-<sha1(kernel/bfx.c)[:10]>
    kept = sorted(kd.glob('best-*.bfx'), key=lambda p: int(p.stem.split('-')[1]))
    return cands, {'kernel_settings': cfg, 't_last_improvement': t_imp, 'kernel_bin': kb.name, 'kernel_stats': ks,
                   'bests_kept': len(kept), 'bests_dir': str(kd)}


class OpError(Exception):
    pass


class FilterAudit:
    """$BOOLFLUX_FILTER_AUDIT=1 (default off: it cleans every candidate an operator tries, which costs CPU):
    how the operator's raw would_place filter compares with the cleaned circuit that admission would judge.
    Counts tried, raw_places, clean_places, lost_by_raw (cleaned places, raw does not), raw_only, dup_id
    (cleaned circuit already archived), dup_skey (its structure already archived).  Never changes a decision."""
    def __init__(self, ar):
        self.on = os.environ.get('BOOLFLUX_FILTER_AUDIT') == '1'; self.ar = ar
        self.n = dict.fromkeys(('tried', 'raw_places', 'clean_places', 'lost_by_raw', 'raw_only', 'dup_id', 'dup_skey'), 0)

    def see(self, c, m, raw_ok):
        if not self.on: return
        from .common import clean, structure_key
        n = self.n; n['tried'] += 1
        cc = clean(c); mc = metrics(cc) if cc is not c else m
        ok = self.ar.would_place(mc)
        n['raw_places'] += raw_ok; n['clean_places'] += ok
        n['lost_by_raw'] += ok and not raw_ok; n['raw_only'] += raw_ok and not ok
        if ok or raw_ok:
            if cid(cc) in self.ar.rec: n['dup_id'] += 1
            elif structure_key(cc) in self.ar.skeys(): n['dup_skey'] += 1

    def info(self):
        return dict(self.n) if self.on else None


def applicability(info):
    """instrumentation (no candidates): {'applicable': False, 'na_reason': ...} when the operator said it does not
    apply (info 'skip') or every try failed with an error (info 'tried' entries 'error...'); else applicable True"""
    if info.get('skip'): return {'applicable': False, 'na_reason': str(info['skip'])}
    tr = info.get('tried')
    if isinstance(tr, list) and tr:
        errs = [x[1] for x in tr if isinstance(x, (list, tuple)) and len(x) > 1 and isinstance(x[1], str) and x[1].startswith('error')]
        if len(errs) == len(tr): return {'applicable': False, 'na_reason': errs[0][:120], 'na_count': len(errs)}
    return {'applicable': True}


def archive_state(ar):
    """the archive state an operator loaded (to replay its filter decisions)"""
    return {'records': len(ar.rec), 'cells': len(ar.cells), 'front': len(ar.front()),
            'max_t_admit': max((r['t_admit'] for r in ar.rec.values()), default=None)}


RUN = None                                 # the job's runlog.RunLog (set by main)
KTIME = [0.0, 0]                           # instrumentation: kernel wall seconds and calls of this process


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
    seen = set(); not_placed = 0; dup = 0; stop = 'partners done'; pair_hits = {}   # (instrumentation counters)
    fa = FilterAudit(ar); pstat = []; t_x = ar.rec[args.inp]['t_admit']; marks = join_marks(getattr(args, 'archive', None)); repeated = 0
    for pid in partners:
        if time.time() - t0 > args.seconds: stop = 'time'; break
        tp = time.time(); y0 = tried; k0 = len(kept)
        P = J.Prepared(ar.circuit(pid), pid)
        for F, B in ((X, P), (P, X)):
            for c, LX, LY, nint in J.join_all(F, B):
                tried += 1
                m = metrics(c); ok = ar.would_place(m); fa.see(c, m, ok)
                if not ok: not_placed += 1; continue
                k = core.to_kernel(c)
                if k in seen: dup += 1; continue
                seen.add(k); pair_hits[pid] = pair_hits.get(pid, 0) + 1
                kept.append((ar.gain(m), c, {'front': F.id, 'back': B.id, 'LX': LX, 'LY': LY, 'interface_gates': nint}))
        done += 1
        if marks.get(pid, -1.0) >= t_x: repeated += 1         # pid's own join passes already met the input
        pstat.append((time.time() - tp, tried - y0, len(kept) - k0))
        if args.since is not None: through = ar.rec[pid]['t_admit']
    if args.since is not None and done == len(partners): through = max(t_load, args.since)
    kept.sort(key=lambda x: -x[0])
    dropped = max(0, len(kept) - args.max_cands)
    kept = kept[:args.max_cands]
    import hashlib
    pacc = {'partner_hash': hashlib.sha1(','.join(sorted(partners)).encode()).hexdigest()[:16],
            'repeated_pairs': repeated, 'partner_s_sum': round(sum(x[0] for x in pstat), 3),
            'partner_s_max': round(max((x[0] for x in pstat), default=0.0), 3),
            'yields_max': max((x[1] for x in pstat), default=0), 'kept_max': max((x[2] for x in pstat), default=0),
            'partners_with_yields': sum(1 for x in pstat if x[1])}
    if RUN is not None:
        RUN.event('join-end', stop=stop, partners=len(partners), partners_done=done, tried=tried, not_placed=not_placed,
                  duplicate=dup, kept=len(kept), kept_over_limit=dropped, partners_with_hits=len(pair_hits),
                  seconds=round(time.time() - t0, 2), **pacc)
    return [c for g, c, d in kept], {'partners': len(partners), 'partners_done': done, 'tried': tried, 'kept_over_limit': dropped,
                                    'since': args.since, 'joined_through': through, 'joins': [d for g, c, d in kept],
                                    'stop': stop, 'not_placed': not_placed, 'duplicate': dup,
                                    'partners_with_hits': len(pair_hits), 'pair_accounting': pacc,
                                    'filter': dict(fa.info() or {}, kept=len(kept), dropped_over_max_cands=dropped) if fa.on else None}


def join_marks(archive_dir):
    """target id -> latest join mark (DIR/stats.jsonl, written by the scheduler): every circuit admitted up to the
    mark has been joined with that target (instrumentation: repeated (target, partner) pair computations)"""
    out = {}
    if archive_dir is None: return out
    try:
        with open(Path(archive_dir) / 'stats.jsonl') as f:
            for ln in f:
                if '"join_mark": null' in ln or '"join"' not in ln: continue
                try:
                    x = json.loads(ln)
                except ValueError:
                    continue
                if x.get('op') == 'join' and isinstance(x.get('join_mark'), (int, float)):
                    out[x['target']] = max(out.get(x['target'], 0.0), x['join_mark'])
    except OSError:
        pass
    return out


def op_trb(ar, args, rng, out):
    from . import trb_impl
    c = ar.circuit(args.inp); A, AD, G, GD = metrics(c)
    t0 = time.time(); best = {}; reps = 0; errors = {}
    fa = FilterAudit(ar); c_m = (A, AD, G, GD); by = {}; hg = {}; hgd = {}                 # instrumentation: per (region, GD cap offset) outcome counts; dG, dGD of built circuits
    while time.time() - t0 < args.seconds:
        D = GD - rng.choice([0, 0, 1])
        kind = rng.choice(['bottom', 'top', 'mid', 'random', 'random'])
        try:
            nc, info = trb_impl.rebuild(c, D, kind, rng)
        except Exception as e:
            k = type(e).__name__; errors[k] = errors.get(k, 0) + 1
            continue
        reps += 1
        b = by.setdefault('%s/-%d' % (kind, GD - D), {})
        if nc is c:
            k = 'skip: ' + (info.get('why') or ('region < 2 gates' if info.get('region_gates', 2) < 2 else 'unchanged'))
            b[k] = b.get(k, 0) + 1; continue
        m = metrics(nc); m0 = c_m; ok = ar.would_place(m); fa.see(nc, m, ok)
        dg = m[2] - m0[2]; dgd = m[3] - m0[3]
        hg['%+d' % max(-6, min(6, dg))] = hg.get('%+d' % max(-6, min(6, dg)), 0) + 1
        hgd['%+d' % max(-6, min(6, dgd))] = hgd.get('%+d' % max(-6, min(6, dgd)), 0) + 1
        if not ok:
            k = 'built: same tuple' if m == m0 else ('built: worse G' if dg > 0 else ('built: better G' if dg < 0 else 'built: same G'))
            k += ', not placed'
            b[k] = b.get(k, 0) + 1; continue
        b['built: would_place'] = b.get('built: would_place', 0) + 1
        best[core.to_kernel(nc)] = nc
        if rng.random() < 0.5: c = nc; c_m = m          # chain rebuilds sometimes
    el = time.time() - t0
    stats = {k: dict(sorted(v.items())) for k, v in sorted(by.items())}
    if RUN is not None:
        RUN.event('trb-end', reps=reps, distinct=len(best), errors=errors, by_region=stats, dG=hg, dGD=hgd,
                  reps_per_s=round(reps / el, 1) if el > 0 else None, seconds=round(el, 2))
    return list(best.values())[:args.max_cands], {'reps': reps, 'rebuild_errors': errors, 'by_region': stats, 'dG': hg, 'dGD': hgd,
                                                  'reps_per_s': round(reps / el, 1) if el > 0 else None,
                                                  'filter': dict(fa.info() or {}, kept=len(best)) if fa.on else None}


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
    mono_main = time.monotonic()            # instrumentation: process start -> main, setup, operator, record (record.json 'timing')
    age_main = runlog.proc_age_s()          # interpreter start + imports
    ap = argparse.ArgumentParser(prog='op_' + name)
    ap.add_argument('--archive', required=True); ap.add_argument('--in', dest='inp', required=True)
    ap.add_argument('--in2'); ap.add_argument('--caps')
    ap.add_argument('--objective', default=DEFAULT_OBJECTIVE)
    ap.add_argument('--seed', type=int, default=1); ap.add_argument('--seconds', type=float, default=60)
    ap.add_argument('--partners', type=int, default=300, help='join without --since: partner limit (legacy pool)')
    ap.add_argument('--since', type=float, default=None,
                    help='join: partners = every cell member admitted after this time (0 = all); omit for the legacy pool')
    ap.add_argument('--max-cands', type=int, default=40)
    ap.add_argument('--function', choices=aesfn.NAMES, default=None,
                    help='aes-sbox or aes-invsbox (default: $BOOLFLUX_FUNCTION, which the scheduler sets, else aes-sbox)')
    ap.add_argument('--out', required=True)
    args = ap.parse_args(argv)
    if args.function: aesfn.use(args.function)
    if args.caps: args.caps = parse_caps(args.caps)
    OBJ.parse(args.objective)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    if any(out.glob('cand-*.bfx')): raise SystemExit('--out %s already holds candidates: a job directory is used once' % out)
    global RUN
    RUN = runlog.RunLog(out, 'hub.op.' + name,
                        seeds={'seed': args.seed, 'rng': 'random.Random(seed): pull cap choice, join partner order, trb regions',
                               'kernel_seed': args.seed if name in ('polish', 'pull') else None},
                        config={k: v for k, v in vars(args).items() if k != 'out'}, budget_s=args.seconds,
                        function=aesfn.name())
    for i in [args.inp] + ([args.in2] if args.in2 else []):
        RUN.add_start(Path(args.archive) / 'archive' / (i + '.bfx'), label='archive member %s' % i, write=False)
    RUN.write()
    rng = random.Random(args.seed)
    t0 = time.time(); r0 = resource.getrusage(resource.RUSAGE_SELF); c0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    mono_t0 = time.monotonic()
    cands, info, error = [], {}, None; archive_load_s = None
    try:
        ta = time.monotonic(); ar = Archive(args.archive); archive_load_s = time.monotonic() - ta
        if args.inp not in ar.rec: raise OpError('--in %s is not in the archive' % args.inp)
        if args.in2 and args.in2 not in ar.rec: raise OpError('--in2 %s is not in the archive' % args.in2)
        loaded = archive_state(ar)
        cands, info = OPS[name](ar, args, rng, out)
        if isinstance(info, dict):
            info.setdefault('archive_loaded', loaded)
            if not cands: info.update(applicability(info))
    except Exception as e:
        import traceback
        traceback.print_exc(); error = '%s: %s' % (type(e).__name__, e); cands = []
    ids = []
    for k, c in enumerate(cands):
        (out / ('cand-%03d.bfx' % k)).write_text(core.to_kernel(c)); ids.append(cid(c))
        RUN.event('candidate', file='cand-%03d.bfx' % k, id=ids[-1], metrics=dict(zip(('A', 'AD', 'G', 'GD'), metrics(c))))
    r1 = resource.getrusage(resource.RUSAGE_SELF); c1 = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu = (r1.ru_utime + r1.ru_stime - r0.ru_utime - r0.ru_stime) + (c1.ru_utime + c1.ru_stime - c0.ru_utime - c0.ru_stime)
    rec = {'operator': name, 'inputs': [args.inp] + ([args.in2] if args.in2 else []), 'caps': args.caps,
           'objective': args.objective, 'seed': args.seed, 'seconds': args.seconds, 'wall_s': round(time.time() - t0, 2),
           'cpu_s': round(cpu, 2), 'candidates': len(cands), 'cand_ids': ids, 'code_version': code_version(), 'info': info,
           'function': aesfn.name(), 'run': RUN.summary()}
    if error: rec['error'] = error
    rec['timing'] = {'mono_main': round(mono_main, 4), 'mono_t0': round(mono_t0, 4), 'mono_end': round(time.monotonic(), 4),
                     'setup_s': round(mono_t0 - mono_main, 3), 'op_s': round(time.monotonic() - mono_t0, 3),
                     'proc_start_to_main_s': age_main, 'archive_load_s': round(archive_load_s, 3) if archive_load_s is not None else None,
                     'kernel_s': round(KTIME[0], 3), 'kernel_calls': KTIME[1]}
    (out / 'record.json').write_text(json.dumps(rec, indent=1, default=str))
    RUN.finish('error' if error else 'ok', candidates=len(cands), error=error)
    return 1 if error else 0
