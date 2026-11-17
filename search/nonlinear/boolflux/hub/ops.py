"""Hub operators.  Common CLI (op_<name>.py):

    op_<name>.py --archive DIR --in ID [--in2 ID] [--caps A,AD,GD] [--objective KEYS] --seed S --seconds T --out JOBDIR

Each writes candidate circuits JOBDIR/cand-*.bfx and JOBDIR/record.json (operator, inputs, settings,
seed, timing, candidate count, code version), and the run record JOBDIR/run.json + events.jsonl.gz
(runlog.py: command, git state, seeds, kernel, host; every kernel improvement and every candidate).
Operators never admit; the scheduler verifies and admits.  The function (aes-sbox or aes-invsbox)
is the process's ($BOOLFLUX_FUNCTION, set by the scheduler, or --function).
  polish  gate kernel (bfx, strict lexicographic objective) under the given caps (default: the input's own)
  pull    the same with one cap lowered (--lower: GD by 1-3 by default; AD or A by 1 on request; repair mode)
  join    transplants of the input (and of the --batch targets) with archive partners in both roles (join.py)
  trb     timing-aware XOR-region rebuilds (trb_impl.py) under the input's GD (--gd-offsets)
polish and pull take --kopt 'KEY=VAL,...' (KOPT_KEYS: pair_xor, tgt_w.mffc1, tgt_w.and, tgt_w.viol, stop_stall_it, T0) over
the kernel defaults; the scheduler sets it per operator (--kopt, --kopt-first).
polish and pull return the kernel's final best and, with --bests N (default 8), up to N of its intermediate
bests (keep_bests): cleaned, placeable in the archive, not archived (id or structure), 4-D Pareto among
themselves and the final, best value first.  join, trb (and linres) judge every candidate after cleaning
(placeable()), as admission does.
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

from .common import aesfn, core, metrics, code_version, cid, clean, structure_key, HUB, PKG
from .. import objective as OBJ
from .. import runlog
from .archive import Archive, pareto
from . import join as J

KDEFAULTS = {'T0': 0.6, 'Tperiod_it': 20000, 'stall_it': 60000, 'uphill': 1.0, 'max_excess': 8,
             'mv.resub1': 1, 'mv.resub2': 2, 'mv.resub3': 1, 'dmax': 220, 'pdiv': 90,
             'nl_samples': 12, 'cand_cap': 40, 'fraig': 1}
KEYW = OBJ.WKEY
DEFAULT_OBJECTIVE = 'a,ad,cost,gd'        # research priorities: AND count, AND depth, then G, GD
# Kernel behaviour options an operator job may set (--kopt KEY=VAL,...; the scheduler's --kopt / --kopt-first pass
# them per operator, 2026-11-17 idea 10).  All default off in the kernel (W1, phase 2): pair_xor 1 (same candidates,
# fewer probes), tgt_w.* (weighted target draw), stop_stall_it N (end the job N iterations after the last new best).
KOPT_KEYS = {'pair_xor': int, 'tgt_w.mffc1': float, 'tgt_w.and': float, 'tgt_w.viol': float, 'stop_stall_it': int,
             'T0': float}       # T0 0: pure plateau walk, no uphill steps (idea 04's observation on mature forward circuits)


def parse_kopt(text):
    """'KEY=VAL,KEY=VAL' -> {KEY: VAL} with KEY in KOPT_KEYS (values checked by type; '' -> {})"""
    out = {}
    for part in (text or '').split(','):
        part = part.strip()
        if not part: continue
        if '=' not in part: raise ValueError('kernel option wants KEY=VAL, got %r' % part)
        k, v = (x.strip() for x in part.split('=', 1))
        if k not in KOPT_KEYS: raise ValueError('unknown kernel option %r (known: %s)' % (k, ', '.join(sorted(KOPT_KEYS))))
        try:
            x = KOPT_KEYS[k](v)
        except ValueError:
            raise ValueError('kernel option %s wants %s, got %r' % (k, KOPT_KEYS[k].__name__, v))
        if x < 0: raise ValueError('kernel option %s must be >= 0' % k)
        out[k] = x
    return out


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


def _kernel(c, caps, objective, seed, seconds, out, archive_dir, kopt=None):
    sp = out / 'start.bfx'; sp.write_text(core.to_kernel(c))
    bp = out / 'best.bfx'; cp = out / 'kernel.cfg'
    cfg = dict(KDEFAULTS)
    cfg.update(kopt or {})                  # --kopt (parse_kopt: only KOPT_KEYS)
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


def placeable(ar, c, slack=None):
    """(cleaned circuit, its metrics, status) as admission will judge c: status 'ok' (would be placed),
    'not placed', 'archived' (the cleaned circuit is an archive member) or 'archived structure' (same DAG
    as a member).  Before 2026-11-16 the operators filtered on the raw metrics and offered exact copies (U7 #2)."""
    cc = clean(c); m = metrics(cc)
    if not ar.would_place(m, slack): return cc, m, 'not placed'
    if cid(cc) in ar.rec: return cc, m, 'archived'
    if structure_key(cc) in ar.skeys(): return cc, m, 'archived structure'
    return cc, m, 'ok'


def _best_no(p):
    t = p.stem.split('-')[-1]
    return int(t) if t.isdigit() else 0


def with_bests(ar, cands, info, limit):
    """the kernel's final best (cands, unchanged) + up to `limit` intermediate bests of the run (info
    bests_dir, the kernel's keep_bests files): placeable, distinct tuples, non-dominated among themselves and the
    final (4-D), highest archive gain first.  The kernel ranks lexicographically under caps, the archive keeps
    4-D cells without caps, so passed bests can be new cells or front points (U7 #1: 41 placeable, 7 with front
    gain in 541 inverse jobs).  info['bests']: counts."""
    d = info.get('bests_dir')
    st = {'files': 0, 'ok': 0, 'not placed': 0, 'archived': 0, 'archived structure': 0, 'unreadable': 0, 'returned': 0}
    info['bests'] = st
    if not limit or not d or not Path(d).is_dir(): return cands
    fm = metrics(clean(cands[0])) if cands else None
    by_m = {}
    for f in sorted(Path(d).glob('best-*.bfx'), key=_best_no):
        st['files'] += 1
        try:
            c = core.from_kernel(f.read_text(), f.stem)
        except Exception:
            st['unreadable'] += 1; continue
        cc, m, why = placeable(ar, c); st[why] += 1
        if why == 'ok' and m != fm and m not in by_m: by_m[m] = (cc, f.name)
    fr = set(pareto(list(by_m) + ([fm] if fm else [])))
    keep = sorted((m for m in by_m if m in fr), key=lambda m: (-ar.gain(m), m))[:limit]
    st['returned'] = len(keep); st['returned_metrics'] = [list(m) + [by_m[m][1]] for m in keep]
    return list(cands) + [by_m[m][0] for m in keep]


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
    cands, info = _kernel(c, caps, args.objective, args.seed, args.seconds, out, args.archive, getattr(args, 'kopt', None))
    info['caps'] = caps
    return with_bests(ar, cands, info, getattr(args, 'bests', 0)), info


PULL_LOWER = 'GD'       # default draw of op_pull (until 2026-11-16 'GD,GD,GD,AD,A': the A and AD draws met their
                        # lowered cap in 0 of 105 inverse jobs, U2 section 6)


def op_pull(ar, args, rng, out):
    c = ar.circuit(args.inp); A, AD, G, GD = metrics(c)
    caps = dict(args.caps or {'A': A, 'AD': AD, 'GD': GD})
    modes = [x.strip() for x in (getattr(args, 'lower', None) or PULL_LOWER).split(',') if x.strip()]
    if not modes or any(x not in ('GD', 'AD', 'A') for x in modes): raise OpError('--lower wants GD, AD, A: %r' % (args.lower,))
    which = modes[0] if len(modes) == 1 else rng.choice(modes)
    if which == 'GD': caps['GD'] = max(1, GD - rng.choice([1, 1, 2, 3])); caps['AD'] = None
    elif which == 'AD': caps['AD'] = max(1, AD - 1)
    else: caps['A'] = max(1, A - 1)
    cands, info = _kernel(c, caps, args.objective, args.seed, args.seconds, out, args.archive, getattr(args, 'kopt', None))
    info.update({'caps': caps, 'lowered': which})
    return with_bests(ar, cands, info, getattr(args, 'bests', 0)), info


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


def parse_batch(text):
    """--batch 'ID:SINCE,ID:SINCE' -> [(id, since)]"""
    out = []
    for part in (text or '').split(','):
        if part.strip():
            i, t = part.strip().split(':', 1); out.append((i, float(t)))
    return out


def op_join(ar, args, rng, out):
    """The input (and every --batch target, in order, while time lasts) against archive partners in both roles
    (join_partners); keeps candidates that admission would place after cleaning (placeable), not archived.
    info['joined_through'] (the input) and info['joined_through_by'] {target: t}: every partner admitted up
    to t has been joined with that target (the scheduler passes it back as --since).  --max-cands is met at a
    partner boundary: a partner whose candidates would overflow it is left for the next job (the mark stops at
    the last partner kept in full; until 2026-11-16 the mark advanced past dropped candidates, U7 #3)."""
    targets = [(args.inp, args.since)] + parse_batch(getattr(args, 'batch', None))
    for i, t in targets[1:]:
        if i not in ar.rec: raise OpError('--batch %s is not in the archive' % i)
    t_load = max((r['t_admit'] for r in ar.rec.values()), default=0.0)
    t0 = time.time(); tried = 0; kept = []; seen = set(); stop = 'partners done'
    not_placed = 0; dup = 0; archived = 0; dropped = 0; deferred = 0; pair_hits = {}     # (instrumentation counters)
    fa = FilterAudit(ar); pstat = []; marks = join_marks(getattr(args, 'archive', None)); repeated = 0
    per = []; all_partners = []
    for ti, (tid, since) in enumerate(targets):
        if ti and (stop != 'partners done' or time.time() - t0 > args.seconds): break
        X = J.Prepared(ar.circuit(tid), tid); t_x = ar.rec[tid]['t_admit']
        partners = join_partners(ar, tid, since, rng, args.partners); all_partners += partners
        through = since; done = 0
        for pid in partners:
            if time.time() - t0 > args.seconds: stop = 'time'; break
            tp = time.time(); y0 = tried; new = []
            P = J.Prepared(ar.circuit(pid), pid)
            for F, B in ((X, P), (P, X)):
                for c, LX, LY, nint in J.join_all(F, B):
                    tried += 1
                    if fa.on: fa.see(c, metrics(c), ar.would_place(metrics(c)))
                    cc, m, why = placeable(ar, c)
                    if why == 'not placed': not_placed += 1; continue
                    if why != 'ok': archived += 1; continue
                    k = structure_key(cc)                 # same structure within the job (also across --batch targets)
                    if k in seen: dup += 1; continue
                    seen.add(k)
                    new.append((ar.gain(m), cc, {'front': F.id, 'back': B.id, 'LX': LX, 'LY': LY, 'interface_gates': nint}))
            if kept and len(kept) + len(new) > args.max_cands:
                stop = 'max_cands'; deferred += len(new); break      # this partner goes to the next job
            if len(new) > args.max_cands:                                # one partner alone: its best are kept
                new.sort(key=lambda x: -x[0]); dropped += len(new) - args.max_cands; new = new[:args.max_cands]
            kept += new; done += 1
            if new: pair_hits[(tid, pid)] = len(new)
            if marks.get(pid, -1.0) >= t_x: repeated += 1         # pid's own join passes already met this target
            pstat.append((time.time() - tp, tried - y0, len(new)))
            if since is not None: through = ar.rec[pid]['t_admit']
        if since is not None and done == len(partners): through = max(t_load, since)
        per.append({'target': tid, 'since': since, 'partners': len(partners), 'partners_done': done, 'joined_through': through})
    kept.sort(key=lambda x: -x[0])
    import hashlib
    pacc = {'partner_hash': hashlib.sha1(','.join(sorted(all_partners)).encode()).hexdigest()[:16],
            'repeated_pairs': repeated, 'partner_s_sum': round(sum(x[0] for x in pstat), 3),
            'partner_s_max': round(max((x[0] for x in pstat), default=0.0), 3),
            'yields_max': max((x[1] for x in pstat), default=0), 'kept_max': max((x[2] for x in pstat), default=0),
            'partners_with_yields': sum(1 for x in pstat if x[1])}
    p0 = per[0]
    if RUN is not None:
        RUN.event('join-end', stop=stop, targets=len(per), partners=sum(x['partners'] for x in per),
                  partners_done=sum(x['partners_done'] for x in per), tried=tried, not_placed=not_placed,
                  duplicate=dup, archived=archived, kept=len(kept), kept_over_limit=dropped, deferred=deferred,
                  partners_with_hits=len(pair_hits), seconds=round(time.time() - t0, 2), **pacc)
    return [c for g, c, d in kept], {'partners': p0['partners'], 'partners_done': p0['partners_done'], 'tried': tried,
                                    'kept_over_limit': dropped, 'deferred': deferred, 'since': args.since,
                                    'joined_through': p0['joined_through'],
                                    'joined_through_by': {x['target']: x['joined_through'] for x in per if x['since'] is not None},
                                    'batch': per, 'joins': [d for g, c, d in kept],
                                    'stop': stop, 'not_placed': not_placed, 'duplicate': dup, 'archived': archived,
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
                if ('"join_mark": null' in ln and '"join_marks": {' not in ln) or '"join"' not in ln: continue
                try:
                    x = json.loads(ln)
                except ValueError:
                    continue
                if x.get('op') == 'join' and isinstance(x.get('join_mark'), (int, float)):
                    out[x['target']] = max(out.get(x['target'], 0.0), x['join_mark'])
                for t, v in (x.get('join_marks') or {}).items():         # batch join jobs (2026-11-16)
                    if isinstance(v, (int, float)): out[t] = max(out.get(t, 0.0), v)
    except OSError:
        pass
    return out


def op_trb(ar, args, rng, out):
    from . import trb_impl
    c = ar.circuit(args.inp); A, AD, G, GD = metrics(c)
    t0 = time.time(); best = {}; reps = 0; errors = {}
    fa = FilterAudit(ar); c_m = (A, AD, G, GD); by = {}; hg = {}; hgd = {}                 # instrumentation: per (region, GD cap offset) outcome counts; dG, dGD of built circuits
    # GD cap offsets (--gd-offsets, default '0' = the input's GD; until 2026-11-16 '0,0,1': the D = GD-1 draws were an
    # infeasible start in 98% of the reps on mature fronts, U2 section 4)
    offs = [int(x) for x in str(getattr(args, 'gd_offsets', None) or TRB_GD_OFFSETS).split(',') if x.strip()]
    while time.time() - t0 < args.seconds:
        D = GD - (offs[0] if len(offs) == 1 else rng.choice(offs))
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
        if fa.on: fa.see(nc, metrics(nc), ar.would_place(metrics(nc)))
        nc, m, why = placeable(ar, nc); m0 = c_m; ok = why == 'ok'
        dg = m[2] - m0[2]; dgd = m[3] - m0[3]
        hg['%+d' % max(-6, min(6, dg))] = hg.get('%+d' % max(-6, min(6, dg)), 0) + 1
        hgd['%+d' % max(-6, min(6, dgd))] = hgd.get('%+d' % max(-6, min(6, dgd)), 0) + 1
        if why.startswith('archived'):
            b['built: ' + why] = b.get('built: ' + why, 0) + 1; continue
        if not ok:
            k = 'built: same tuple' if m == m0 else ('built: worse G' if dg > 0 else ('built: better G' if dg < 0 else 'built: same G'))
            k += ', not placed'
            b[k] = b.get(k, 0) + 1; continue
        b['built: would_place'] = b.get('built: would_place', 0) + 1
        best[structure_key(nc)] = (nc, m)
        if rng.random() < 0.5: c = nc; c_m = m          # chain rebuilds sometimes
    el = time.time() - t0
    stats = {k: dict(sorted(v.items())) for k, v in sorted(by.items())}
    if RUN is not None:
        RUN.event('trb-end', reps=reps, distinct=len(best), errors=errors, by_region=stats, dG=hg, dGD=hgd,
                  reps_per_s=round(reps / el, 1) if el > 0 else None, seconds=round(el, 2))
    out_c = [c2 for c2, m2 in sorted(best.values(), key=lambda cm: (-ar.gain(cm[1]), cm[1]))[:args.max_cands]]   # best first (was: first found)
    return out_c, {'reps': reps, 'rebuild_errors': errors, 'by_region': stats, 'dG': hg, 'dGD': hgd,
                                                  'reps_per_s': round(reps / el, 1) if el > 0 else None,
                                                  'filter': dict(fa.info() or {}, kept=len(best)) if fa.on else None}


TRB_GD_OFFSETS = '0'
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
    ap.add_argument('--batch', help="join: more targets 'ID:SINCE,...' joined after --in in the same job (scheduler batches)")
    ap.add_argument('--lower', help="pull: cap(s) to lower, drawn uniformly: 'GD' (default) or 'GD,GD,GD,AD,A' (until 2026-11-16)")
    ap.add_argument('--gd-offsets', help="trb: GD cap offsets below the input's GD, drawn uniformly (default '0'; until 2026-11-16 '0,0,1')")
    ap.add_argument('--bests', type=int, default=8, help='polish/pull: intermediate kernel bests returned besides the final (0: final only)')
    ap.add_argument('--kopt', default='', help="polish/pull: kernel options 'KEY=VAL,...' over the defaults (keys: %s)" % ', '.join(sorted(KOPT_KEYS)))
    ap.add_argument('--function', choices=aesfn.NAMES, default=None,
                    help='aes-sbox or aes-invsbox (default: $BOOLFLUX_FUNCTION, which the scheduler sets, else aes-sbox)')
    ap.add_argument('--out', required=True)
    args = ap.parse_args(argv)
    if args.function: aesfn.use(args.function)
    if args.caps: args.caps = parse_caps(args.caps)
    try:
        args.kopt = parse_kopt(args.kopt)
    except ValueError as e:
        raise SystemExit('--kopt: %s' % e)
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
