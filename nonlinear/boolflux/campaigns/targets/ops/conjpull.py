#!/usr/bin/env python3
"""conjpull: GF(2^8) conjugate + staged kernel pull operator (general form of P3's conj3/mkconj/pdrive
pipeline and P6's t07c3 pipeline).

    python3 nonlinear/boolflux/campaigns/targets/ops/conjpull.py --in START --target Txx --seed S \
        --seconds T --out DIR [--cpus 1]
        [--conj ITEMS]            comma list, processed in order until the time ends:
                                    id            the start itself (no conjugation)
                                    L:K           conjugate lam L, k K (x -> L x^(2^K))
                                    rank:R        the R-th best non-identity conjugate by the conj3 score
                                    top:N         ranks 1..N;   all = all 2039 non-identity, by score
                                  default rank:1
        [--schedule STAGES]       comma list MODE:CAPGD:SECONDS[:rk0|rk1]; default g:31:200,m:27:200,m:25:200
                                    g gate (fdrive gate: kernel restarted from the stage best)
                                    m mix (fdrive mix: gate / osc / trb rotation)   o osc   t trb
                                    k one hub-style kernel run, objective cost,gd (P6 kern.py)
                                  CAPGD may be +N / -N: relative to the GD of the stage's input
        [--beam B]                seeds per stage (sequential on this CPU); the best (feasible at the
                                  stage cap, then G, GD) goes on; default 1
        [--repair-keep 0|1]       kernel repair_keep for every stage without its own rk flag; default 1
        [--kcfg KEY=VAL ...]      extra kernel settings (e.g. T0=0.8 stall_it=80000)
        [--stage-iters N] [--relax R] [--repair-iters N] [--trb-regions LIST] [--top-runs N]
        [--screen-cache DIR]      conj3 screen cache (shared, per start sha256); default NIGHT/cache/conj3

Search states may exceed the A, AD, G and GD caps (user, 2026-11-15 23:50 UTC): the stage caps are
kernel caps on GD only plus the target's A/AD as kernel caps, the stage input may be above them
(repair), and only RECORDED circuits must be inside A <= ref A, AD <= ref AD (common.Recorder).  Every
kernel output, osc-relaxed state and trb rebuild inside the hard limits is offered to the recorder,
which writes each new job-local Pareto point (aes_check, sidecar) at once.

Method (P3 NOTES "Conjugates"; P6 NOTES s.12-13): inv = H o inv o G for G(z) = lam z^(2^k), so every
circuit has 2040 conjugates with the same AND structure; only the top linear layer (forms f -> f o G)
and the output layer (Mout) change.  conj3 scores each by a BP top proxy + Paar bottom proxy; mkconj
builds one (BP top resynthesis, trb top/bottom passes).  The kernel then finds other XOR layers in the
new linear basis: loose GD cap in gate mode first, then mix stages at tighter caps.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import random
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common as CM                                  # noqa: E402

STRAT = CM.PKG / 'strategies'
for d in ('P3', 'F', 'T2'):
    sys.path.append(str(STRAT / d))
from boolflux import core                            # noqa: E402
from boolflux.hub.common import clean                # noqa: E402

OP = 'conjpull'
# fdrive / P3 pdrive kernel defaults (strategies/P3/pdrive.py DEFAULTS); repair_keep set per stage
FDEF = {'T0': 0.6, 'Tperiod_it': 20000, 'stall_it': 60000, 'uphill': 1.0, 'max_excess': 8,
        'mv.resub1': 1, 'mv.resub2': 2, 'mv.resub3': 1, 'dmax': 220, 'pdiv': 90,
        'nl_samples': 12, 'cand_cap': 40, 'fraig': 1, 'w.cost': 1.0, 'w.g': 0.0, 'w.a': 0.0,
        'w.gd': 1e-4, 'w.ad': 0.0}
T_END = None


def now():
    return time.time()


def left():
    return T_END - now()


# ---- conjugate screen (conj3) and build (mkconj) ------------------------------------------------

def screen(c, start_sha, cache_dir, top_runs=4, log=print, offset=0):
    """conj3 score of all 2040 (lam, k); cached per start sha256.  The 8 k-slices are cached separately,
    each under its own lock: concurrent jobs on the same start share the work (a job takes the free
    slices, starting at `offset`, then waits for the slices others hold).  Returns the rows sorted by
    (sum, lam, k)."""
    cache_dir = Path(cache_dir); cache_dir.mkdir(parents=True, exist_ok=True)
    f = cache_dir / ('%s-r%d.json' % (start_sha[:20], top_runs))
    if f.exists():
        return json.loads(f.read_text())['rows']
    t0 = now()
    sl = lambda k: cache_dir / ('%s-r%d-k%d.json' % (start_sha[:20], top_runs, k))
    order = [(offset + i) % 8 for i in range(8)]
    for blocking in (False, True):
        for k in order:
            if sl(k).exists(): continue
            with open(str(sl(k)) + '.lock', 'w') as lk:
                try:
                    fcntl.flock(lk, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
                except BlockingIOError:
                    continue
                if sl(k).exists(): continue
                CM.write_json(sl(k), {'rows': screen_slice(c, k, top_runs)})
    rows = []
    for k in range(8):
        rows += json.loads(sl(k).read_text())['rows']
    rows.sort(key=lambda r: (r['sum'], r['lam'], r['k']))
    if not f.exists():
        CM.write_json(f, {'start_sha256': start_sha, 'top_runs': top_runs, 'utc': CM.utc(), 'rows': rows})
    log('conj3 screen ready after %.0f s -> %s' % (now() - t0, f))
    return rows


def screen_slice(c, k, top_runs):
    """conj3.py main loop for one k (255 lams): BP top proxy + Paar bottom proxy."""
    if True:
        import conj3 as C3
        CJ = C3.CJ
        top, outs, nl = C3.layers(c)
        rows = []
        for k in [k]:
            for lam in range(1, 256):
                G = CJ.matrix(lambda z: CJ.gmul(lam, CJ.gpow(z, 1 << k)))
                Gp = CJ.matrix(lambda w: CJ.gpow(CJ.gmul(lam, w), 1 << ((8 - k) % 8)))
                Mout = CJ.matrix(lambda y: CJ.apply(CJ.A, CJ.apply(Gp, CJ.apply(CJ.Ainv, y))))
                urow = []
                for i in range(8):
                    bit = 7 - i
                    urow.append(sum(1 << (7 - j) for j in range(8) if G[j] >> bit & 1))
                ntop = []
                for t in top:
                    v = 0
                    for i in range(8):
                        if t >> i & 1: v ^= urow[i]
                    ntop.append(v)
                ct = C3.bp_cost(8, ntop, top_runs, random.Random(lam * 8 + k))
                nouts = []
                for i in range(8):
                    bit = 7 - i
                    v = 0
                    for j in range(8):
                        if Mout[j] >> bit & 1: v ^= outs[7 - j]
                    nouts.append(v)
                cb = C3.paar(nouts)
                rows.append({'lam': lam, 'k': k, 'top': ct, 'bot': cb, 'sum': (ct or 99) + cb})
        return rows


def build_conj(c, lam, k, top_runs=12):
    """mkconj.py: naive conjugate circuit, BP top resynthesis, trb top/bottom passes; verified."""
    import conj as CJ
    import bp
    cc = CJ.conj_circuit(c, lam, k)
    best, info = bp.optimise(cc, 99, 'top', random.Random(lam * 8 + k), top_runs, log=lambda *x: None)
    if best is not None: cc = best
    cc = CJ.resynth(cc, random.Random(1), 2)
    assert cc.value_table() == CM.AES, 'conjugate %d:%d wrong function' % (lam, k)
    return cc


def conj_list(spec, c, start_sha, a, log):
    items = []
    rows = None
    def get_rows():
        nonlocal rows
        if rows is None:
            rows = [r for r in screen(c, start_sha, a.screen_cache, a.screen_runs, log, offset=a.seed % 8)
                    if not (r['lam'] == 1 and r['k'] == 0)]
        return rows
    for it in spec.split(','):
        it = it.strip()
        if not it: continue
        if it == 'id':
            items.append(('id', None, None, None))
        elif it == 'all':
            items += [('rank:%d' % (i + 1), r['lam'], r['k'], r['sum']) for i, r in enumerate(get_rows())]
        elif it.startswith('rank:'):
            R = int(it[5:]); r = get_rows()[R - 1]
            items.append((it, r['lam'], r['k'], r['sum']))
        elif it.startswith('top:'):
            N = int(it[4:])
            items += [('rank:%d' % (i + 1), r['lam'], r['k'], r['sum']) for i, r in enumerate(get_rows()[:N])]
        else:
            lam, k = map(int, it.split(':'))
            items.append(('%d:%d' % (lam, k), lam, k, None))
    return items


# ---- kernel stages (fdrive/pdrive semantics, in-process) ----------------------------------------

class Ctx:
    pass


def kernel(ctx, c, capgd, iters, seed, seconds, rk, style='f'):
    """One kernel call; returns the kernel's best circuit (checked to compute the S-box)."""
    if style == 'h':
        from boolflux.hub.ops import KDEFAULTS
        from boolflux import objective as OBJ
        cfg = dict(KDEFAULTS); cfg.update(OBJ.weights('cost,gd'))
    else:
        cfg = dict(FDEF)
    for op, v in CM.MODEL.cost.items(): cfg['cost.%d' % op] = v
    cfg['repair_keep'] = rk
    cfg['cap.gd'] = capgd; cfg['cap.ad'] = ctx.cap['AD']; cfg['cap.a'] = ctx.cap['A']
    cfg.update(ctx.kcfg)
    ctx.ncall += 1
    tag = 'k%d' % ctx.ncall
    sp = ctx.wd / (tag + '.in'); op_ = ctx.wd / (tag + '.out'); cp = ctx.wd / (tag + '.cfg')
    sp.write_text(core.to_kernel(c))
    cfg.update({'in': sp, 'out': op_, 'seed': seed, 'seconds': max(1, int(seconds))})
    if iters: cfg['iters'] = iters
    cp.write_text(''.join('%s %s\n' % kv for kv in cfg.items()))
    m0 = CM.metrics(c)
    inside = m0[0] <= ctx.cap['A'] and m0[1] <= ctx.cap['AD'] and m0[3] <= capgd
    ctx.cert = ctx.cert and (inside or rk == 1)
    try:
        r = subprocess.run([str(ctx.bfx), str(cp)], capture_output=True, text=True, timeout=max(1, seconds) + 30)
        rc = r.returncode
    except subprocess.TimeoutExpired:
        rc = 'timeout'
    out = None
    if rc == 0 and op_.exists():
        out = core.from_kernel(op_.read_text())
        if out.value_table() != CM.AES:
            ctx.log('kernel returned a wrong function (call %d); ignored' % ctx.ncall); out = None
    else:
        ctx.log('kernel call %d exit %s: %s' % (ctx.ncall, rc, (getattr(r, 'stdout', '') or '')[-300:] if rc != 'timeout' else ''))
    for p in (sp, op_, cp):
        try: p.unlink()
        except OSError: pass
    return out


def offer(ctx, c, how):
    if c is None: return
    t = CM.metrics(c)
    if CM.in_limits(t, None, ctx.lim) and not any(all(a <= b for a, b in zip(p, t)) for p in ctx.lin_front):
        ctx.lin_front = [p for p in ctx.lin_front if not all(a <= b for a, b in zip(t, p))] + [t]
        ctx.lin_changed = True                     # the lineage's own (A, AD, G, GD) set changed
    ctx.rec.offer(c, how=how, lineage=list(ctx.lineage) + [how], path_certified=ctx.cert)


def run_stage(ctx, base, mode, D, secs, seed, rk):
    """fdrive main loop (gate / osc / trb / mix / k) for `secs` seconds from `base` at GD cap D.
    Returns the stage best (hard-limit circuits only; feasible at D first, then G, GD)."""
    lim = ctx.cap                     # search caps (default = target limits; --cap-a / --cap-ad tighter)
    met = CM.metrics
    hard = lambda c: met(c)[0] <= lim['A'] and met(c)[1] <= lim['AD']
    feas = lambda c: hard(c) and met(c)[3] <= D
    key = lambda c: (0 if feas(c) else 1, met(c)[2], met(c)[3])
    rng = random.Random(seed)
    t_end = min(now() + secs, T_END - 15)
    best = base; cur = base
    def take(c, how):
        nonlocal best
        if c is None: return
        c = clean(c)                  # structural-hash merge of duplicate gates (function unchanged)
        offer(ctx, c, how)
        if hard(c) and key(c) < key(best): best = c
    sub = 0
    if mode == 'k':
        c = kernel(ctx, base, D, None, seed, max(1, t_end - now()), rk, style='h')
        take(c, 'k%d' % D)
        return best
    while t_end - now() > 2:
        sub += 1
        rem = t_end - now()
        kseed = seed * 100000 + sub
        m = mode
        if m == 'm': m = ['g', 'o', 't'][sub % 3]
        b = best if feas(best) else cur
        if m == 'g':
            c = kernel(ctx, b, D, ctx.a.stage_iters, kseed, rem, rk)
            take(c, 'g%d' % D)
            if c is not None and hard(c): cur = c
        elif m == 'o':
            c1 = kernel(ctx, b, D + ctx.a.relax, ctx.a.stage_iters // 2, kseed, rem / 2, rk)
            take(c1, 'o%d-relaxed%d' % (D, D + ctx.a.relax))
            if c1 is None: continue
            c2 = kernel(ctx, c1, D, ctx.a.repair_iters, kseed + 7, max(1, t_end - now()), rk)
            take(c2, 'o%d-repair' % D)
            if c2 is not None and feas(c2) and t_end - now() > 2:
                c3 = kernel(ctx, c2, D, ctx.a.stage_iters // 2, kseed + 13, max(1, t_end - now()), rk)
                take(c3, 'o%d-gate' % D)
                if c3 is not None and hard(c3): cur = c3
            elif c2 is not None and hard(c2):
                cur = c2
        elif m == 't':
            import trb
            reg = rng.choice(ctx.a.trb_regions.split(','))
            try:
                c1, info = trb.rebuild(b, D, reg, rng)
            except Exception as e:                      # trb raises nothing by contract; be safe
                ctx.log('trb failed: %r' % (e,)); c1 = b
            if c1.value_table() != CM.AES: c1 = b
            take(c1, 't%d-%s-build' % (D, reg))
            c2 = kernel(ctx, c1, D, ctx.a.stage_iters, kseed, max(1, t_end - now()), rk)
            take(c2, 't%d-%s' % (D, reg))
            if c2 is not None and hard(c2): cur = c2
    return best


def is_conjugated(path, depth=0):
    """True if the start's sidecar (or its parent chain, up to 6 links) records a GF(2^8) conjugation:
    a conjpull lineage 'conj lam ..', or a P3/P6 conjugate file name/method (cj-, conj, mkconj)."""
    import re
    p = Path(path)
    name = p.name
    if not name.startswith('conjpull-') and re.search(r'conj(?!pull)|(^|[-_/])cj[-\d]', str(p)):
        return True
    stem = name[:-len('.circ.txt')] if name.endswith('.circ.txt') else p.stem
    j = p.with_name(stem + '.json')
    if not j.exists() or depth > 6: return False
    try: m = json.loads(j.read_text())
    except Exception: return False
    lin = json.dumps(m.get('lineage') or '') + ' ' + json.dumps(m.get('method') or '')
    if 'conj lam' in lin or 'mkconj' in lin or 'conjugate lam' in lin or 'conjugate (' in lin.lower():
        return True
    par = (m.get('parent') or m.get('start') or {})
    par = par.get('path') if isinstance(par, dict) else par
    return bool(par) and Path(par).exists() and Path(par) != p and is_conjugated(par, depth + 1)


def parse_schedule(s):
    st = []
    for x in s.split(','):
        x = x.strip()
        if not x: continue
        p = x.split(':')
        mode, cap, secs = p[0], p[1], float(p[2])
        rk = None; seed = None
        for tok in p[3:]:
            if tok.startswith('rk'): rk = int(tok[2:])
            elif tok.startswith('s'): seed = int(tok[1:])          # explicit stage seed (replays)
            else: raise ValueError('unknown stage option %r in %r' % (tok, x))
        assert mode in ('g', 'm', 'o', 't', 'k'), 'unknown stage mode %r' % mode
        st.append((mode, cap, secs, rk, seed))
    return st


def main(argv=None):
    global T_END
    ap = CM.contract_args(argparse.ArgumentParser(description=__doc__.split('\n')[0]))
    ap.add_argument('--conj', default='rank:1')
    ap.add_argument('--schedule', default='g:31:200,m:27:200,m:25:200')
    ap.add_argument('--beam', type=int, default=1)
    ap.add_argument('--repair-keep', default='1', help='0, 1, or alt (= seed %% 2: matched rk 0/1 comparison across jobs)')
    ap.add_argument('--beam-rk', default='', help='repair_keep per beam seed, e.g. 0,1 (M1: matched comparison)')
    ap.add_argument('--cap-a', type=int, default=None, help='search A cap below the target A (kernel cap.a, stage choice)')
    ap.add_argument('--cap-ad', type=int, default=None, help='search AD cap below the target AD (e.g. T05 AD4 side)')
    ap.add_argument('--stall-stages', type=int, default=2,
                    help='drop the lineage (go to the next conjugate) after N consecutive stages that recorded no '
                         'new point; 0 = off (M1 7.0)')
    ap.add_argument('--allow-reconj', action='store_true', help='conjugate a start whose sidecar lineage is a conjugate')
    ap.add_argument('--kcfg', nargs='*', default=[])
    ap.add_argument('--stage-iters', type=int, default=200000)
    ap.add_argument('--relax', type=int, default=1)
    ap.add_argument('--repair-iters', type=int, default=100000)
    ap.add_argument('--trb-regions', default='bottom,top,mid,random')
    ap.add_argument('--top-runs', type=int, default=12, help='BP runs when building a conjugate (mkconj)')
    ap.add_argument('--screen-runs', type=int, default=4, help='BP runs per conjugate in the conj3 screen')
    ap.add_argument('--screen-cache', default=str(CM.NIGHT / 'cache' / 'conj3'))
    ap.add_argument('--kernel', default=None, help='kernel binary (default: repo build bfx-<sha1(bfx.c)[:10]>)')
    a = ap.parse_args(argv)
    T0 = now(); T_END = T0 + a.seconds
    a.repair_keep = a.seed % 2 if str(a.repair_keep) == 'alt' else int(a.repair_keep)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    logf = open(out / 'conjpull.log', 'a')
    def log(*x):
        logf.write('%s %7.1f %s\n' % (time.strftime('%H:%M:%S', time.gmtime()), now() - T0, ' '.join(map(str, x)))); logf.flush()
    ctx = Ctx(); ctx.a = a; ctx.log = log; ctx.ncall = 0
    ctx.lim = CM.limits(a.target)
    ctx.cap = {'A': min(ctx.lim['A'], a.cap_a or 999), 'AD': min(ctx.lim['AD'], a.cap_ad or 999)}
    ctx.kcfg = {}
    for kv in a.kcfg:
        k, v = kv.split('=', 1)
        try: ctx.kcfg[k] = int(v)
        except ValueError:
            try: ctx.kcfg[k] = float(v)
            except ValueError: ctx.kcfg[k] = v
    ctx.bfx = Path(a.kernel) if a.kernel else CM.kernel_bin()
    ctx.wd = out / 'work'; ctx.wd.mkdir(exist_ok=True)
    sched = parse_schedule(a.schedule)
    beam_rk = [int(x) for x in a.beam_rk.split(',') if x.strip()]
    params = {'conj': a.conj, 'schedule': a.schedule, 'beam': a.beam, 'repair_keep': a.repair_keep, 'beam_rk': beam_rk,
              'kcfg': ctx.kcfg, 'stage_iters': a.stage_iters, 'relax': a.relax, 'repair_iters': a.repair_iters,
              'trb_regions': a.trb_regions, 'top_runs': a.top_runs, 'screen_runs': a.screen_runs,
              'caps': {'A': ctx.lim['A'], 'AD': ctx.lim['AD']}, 'kernel_bin': ctx.bfx.name}
    command = ' '.join([sys.executable, str(Path(__file__).resolve())] + list(argv if argv is not None else sys.argv[1:]))
    method = ('ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged kernel pulls %s '
              '(fdrive semantics; kernel %s, repair_keep %d unless a stage says rk0/rk1); search states may exceed '
              'caps, recorded circuits inside A<=%d AD<=%d' % (a.schedule, ctx.bfx.name, a.repair_keep, ctx.lim['A'], ctx.lim['AD']))
    rec = CM.Recorder(out, OP, a.target, a.inp, a.seed, command, method, params, kernel=ctx.bfx, t0=T0)
    ctx.rec = rec
    stages_log = []

    def on_alarm(sig, frm):
        rec.finish('timeout', {'stages': stages_log})
        os._exit(3)
    signal.signal(signal.SIGALRM, on_alarm); signal.alarm(int(a.seconds + 45))
    signal.signal(signal.SIGTERM, on_alarm)

    status = 'ok'
    try:
        start = CM.load(a.inp)
        assert start.value_table() == CM.AES, 'start does not compute the AES S-box'
        log('start', CM.metrics(start), a.inp, 'kernel', ctx.bfx)
        items = conj_list(a.conj, start, rec.start_sha, a, log)
        if is_conjugated(a.inp) and not a.allow_reconj:
            skipped = [x[0] for x in items if x[1] is not None]
            items = [x for x in items if x[1] is None]
            if skipped:
                rec.notes.append('start is already a conjugate (sidecar lineage); conjugates %s skipped (M1: do not '
                                 're-conjugate; --allow-reconj overrides)%s' % (skipped, '' if items else '; identity pull instead'))
                log(rec.notes[-1])
            if not items:
                items = [('id', None, None, None)]
        for (name, lam, k, score) in items:
            if left() < 30: break
            ctx.cert = True; ctx.lin_front = []; ctx.lin_changed = False; quiet = 0
            if lam is None:
                cc = start; ctx.lineage = ['start']
            else:
                t1 = now()
                cc = build_conj(start, lam, k, a.top_runs)
                ctx.lineage = ['conj lam %d k %d (%s, score %s)' % (lam, k, name, score)]
                log('conjugate', name, lam, k, 'score', score, '->', CM.metrics(cc), '%.1fs' % (now() - t1))
            cur = cc
            ctx.lin_front = [CM.metrics(cc)]          # the lineage's own set starts at its input (not recorded)
            for si, (mode, cap, secs, rk, sseed) in enumerate(sched):
                if left() < 20: break
                if a.stall_stages and quiet >= a.stall_stages:
                    log('lineage dropped: %d stages without a change in its (A, AD, G, GD) set' % quiet)
                    stages_log.append({'conj': name, 'dropped_after_stage': si}); break
                ctx.lin_changed = False
                gd_in = CM.metrics(cur)[3]
                D = gd_in + int(cap) if cap[0] in '+-' else int(cap)
                bests = []
                for j in range(a.beam):
                    if left() < 20: break
                    rkk = rk if rk is not None else (beam_rk[j % len(beam_rk)] if beam_rk else a.repair_keep)
                    sd = (sseed + j) if sseed is not None else a.seed * 1000 + si * 10 + j
                    ctx.lineage.append('stage %d %s:%d:%g seed %d rk %d' % (si + 1, mode, D, secs, sd, rkk))
                    t1 = now()
                    b = run_stage(ctx, cur, mode, D, min(secs, left() - 15), sd, rkk)
                    ctx.lineage.pop()
                    bests.append(b)
                    stages_log.append({'conj': name, 'lam': lam, 'k': k, 'stage': si + 1, 'mode': mode, 'cap': D,
                                       'seed': sd, 'in': list(CM.metrics(cur)), 'best': list(CM.metrics(b)),
                                       'seconds': round(now() - t1, 1)})
                    log('stage', si + 1, mode, D, 'seed', sd, CM.metrics(cur), '->', CM.metrics(b), '%.0fs' % (now() - t1))
                feasD = lambda c: CM.metrics(c)[3] <= D
                bests.sort(key=lambda c: (0 if feasD(c) else 1, CM.metrics(c)[2], CM.metrics(c)[3]))
                if bests:
                    nxt = bests[0]
                    ctx.lineage.append('stage %d %s:%d best %s' % (si + 1, mode, D, '/'.join(map(str, CM.metrics(nxt)))))
                    cur = nxt
                quiet = 0 if ctx.lin_changed else quiet + 1
                rec.write_result({'stages': stages_log})
    except Exception as e:
        import traceback
        status = 'error'; rec.notes.append(traceback.format_exc()[-1500:]); log('ERROR', repr(e))
    signal.alarm(0)
    rec.finish(status, {'stages': stages_log, 'kernel_calls': ctx.ncall})
    log('end', status, 'written', len(rec.points), 'pareto', [p['tuple'] for p in rec.best_points()['pareto_G_GD']])
    return 0 if status == 'ok' else 1


if __name__ == '__main__':
    sys.exit(main())
