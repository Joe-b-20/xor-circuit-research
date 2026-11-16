#!/usr/bin/env python3
"""conjpull: GF(2^8) conjugate + staged kernel pull operator (library: ops/conj_lib/).

    python3 search/nonlinear/boolflux/ops/conjpull.py --in START --target REF --seed S \
        --seconds T --out DIR [--cpus 1]
        [--conj ITEMS]            comma list, processed in order until the time ends:
                                    id            the start itself (no conjugation)
                                    L:K           conjugate lam L, k K (x -> L x^(2^K))
                                    rank:R        the R-th best non-identity conjugate by the conj3 score
                                    top:N         ranks 1..N;   all = all 2039 non-identity, by score
                                  default rank:1
        [--schedule STAGES]       comma list MODE:CAPGD:SECONDS[:rk0|rk1]; default g:31:200,m:27:200,m:25:200
                                    g gate (kernel restarted from the stage best)
                                    m mix (gate / osc / trb rotation)   o osc   t trb
                                    k one hub-style kernel run, objective cost,gd
                                  CAPGD may be +N / -N: relative to the GD of the stage's input
        [--beam B]                seeds per stage (sequential on this CPU); the best (feasible at the
                                  stage cap, then G, GD) goes on; default 1
        [--repair-keep 0|1]       kernel repair_keep for every stage without its own rk flag; default 1
        [--kcfg KEY=VAL ...]      extra kernel settings (e.g. T0=0.8 stall_it=80000)
        [--stage-iters N] [--relax R] [--repair-iters N] [--trb-regions LIST] [--top-runs N]
        [--screen-cache DIR]      conj3 screen cache (shared, per start sha256); default $BOOLFLUX_CACHE/cache/conj3

Search states may exceed the A, AD, G and GD caps: the stage caps are
kernel caps on GD only plus the target's A/AD as kernel caps, the stage input may be above them
(repair), and only RECORDED circuits must be inside A <= ref A, AD <= ref AD (common.Recorder).  Every
kernel output, osc-relaxed state and trb rebuild inside the hard limits is offered to the recorder,
which writes each new job-local Pareto point (aes_check, sidecar) at once.

Method: inv = H o inv o G for G(z) = lam z^(2^k), so every
circuit has 2040 conjugates with the same AND structure; only the top linear layer (forms f -> f o G)
and the output layer (Mout) change.  For the inverse S-box (--function aes-invsbox, or a start that
computes it with the default --function auto) S^-1(y) = G'(S^-1(Lin y + cL)), Lin = A G A^-1: the top
layer goes through the affine map Lin y + cL and the outputs through G' (conj_lib/conj.py maps()).  conj3 scores each by a BP top proxy + Paar bottom proxy; build_conj
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

sys.path.append(str(HERE / 'conj_lib'))           # conjugates, Boyar-Peralta / SAT regions, trb
from boolflux import core, runlog                    # noqa: E402
from boolflux.hub.common import clean                # noqa: E402

OP = 'conjpull'
# kernel defaults of the stages; repair_keep set per stage
FDEF = {'T0': 0.6, 'Tperiod_it': 20000, 'stall_it': 60000, 'uphill': 1.0, 'max_excess': 8,
        'mv.resub1': 1, 'mv.resub2': 2, 'mv.resub3': 1, 'dmax': 220, 'pdiv': 90,
        'nl_samples': 12, 'cand_cap': 40, 'fraig': 1, 'w.cost': 1.0, 'w.g': 0.0, 'w.a': 0.0,
        'w.gd': 1e-4, 'w.ad': 0.0}
T_END = None


def now():
    return time.time()


def left():
    return T_END - now()


# ---- conjugate screen (conj3) and build (build_conj) --------------------------------------------

SCREEN_T = {'compute_s': 0.0, 'wait_s': 0.0, 'slices_computed': 0}


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
                tw = now()
                try:
                    fcntl.flock(lk, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
                except BlockingIOError:
                    continue
                SCREEN_T['wait_s'] += now() - tw          # instrumentation: time waiting for slices other jobs compute
                if sl(k).exists(): continue
                tc = now()
                CM.write_json(sl(k), {'rows': screen_slice(c, k, top_runs)})
                SCREEN_T['compute_s'] += now() - tc; SCREEN_T['slices_computed'] += 1
    rows = []
    for k in range(8):
        rows += json.loads(sl(k).read_text())['rows']
    rows.sort(key=lambda r: (r['sum'], r['lam'], r['k']))
    if not f.exists():
        CM.write_json(f, {'start_sha256': start_sha, 'top_runs': top_runs, 'utc': CM.utc(), 'rows': rows})
    log('conj3 screen ready after %.0f s -> %s' % (now() - t0, f))
    return rows


def screen_slice(c, k, top_runs):
    """conj3.py main loop for one k (255 lams): BP top proxy + Paar bottom proxy.  The input map In
    and output map Out are conj.maps() of the process's function (aes-sbox: G and Mout)."""
    if True:
        import conj3 as C3
        CJ = C3.CJ
        top, outs, nl = C3.layers(c)
        rows = []
        for k in [k]:
            for lam in range(1, 256):
                G, _, Mout, _ = CJ.maps(lam, k)
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


LAST_BUILD = {}           # instrumentation: the intermediate circuits of the last build_conj (naive, BP top)


def build_conj(c, lam, k, top_runs=12):
    """Naive conjugate circuit, BP top resynthesis, trb top/bottom passes; verified."""
    import conj as CJ
    import bp
    cc = CJ.conj_circuit(c, lam, k)
    LAST_BUILD.clear(); LAST_BUILD.update(lam=lam, k=k, naive=cc)
    best, info = bp.optimise(cc, 99, 'top', random.Random(lam * 8 + k), top_runs, log=lambda *x: None)
    if best is not None: cc = best
    LAST_BUILD['bp'] = cc
    cc = CJ.resynth(cc, random.Random(1), 2)
    assert cc.value_table() == CM.AES, 'conjugate %d:%d wrong function' % (lam, k)
    return cc


def conj_list(spec, c, start_sha, a, log):
    items = []
    rows = None
    def get_rows():
        nonlocal rows
        if rows is None:
            t1 = now()
            cached = (Path(a.screen_cache) / ('%s-r%d.json' % (start_sha[:20], a.screen_runs))).exists()
            allrows = screen(c, start_sha, a.screen_cache, a.screen_runs, log, offset=a.seed % 8)
            rows = [r for r in allrows if not (r['lam'] == 1 and r['k'] == 0)]
            a._rows = rows
            # instrumentation: the screen the conjugates are chosen from (score = BP top proxy + Paar bottom proxy)
            ident = next((r for r in allrows if r['lam'] == 1 and r['k'] == 0), None)
            ss = sorted(r['sum'] for r in rows)
            if hasattr(a, '_rec') and a._rec is not None:
                a._rec.log.event('screen', cached=cached, seconds=round(now() - t1, 2), rows=len(rows),
                                 identity=ident, best=ss[0] if ss else None, median=ss[len(ss) // 2] if ss else None,
                                 worst=ss[-1] if ss else None, top10=rows[:10],
                                 n_at_best=sum(1 for x in ss if x == ss[0]) if ss else 0,
                                 compute_s=round(SCREEN_T['compute_s'], 2), wait_s=round(SCREEN_T['wait_s'], 2),
                                 slices_computed=SCREEN_T['slices_computed'])
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


# ---- kernel stages (in-process) ------------------------------------------------------------------

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
    t_call = now()
    try:
        r = subprocess.run([str(ctx.bfx), str(cp)], capture_output=True, text=True, timeout=max(1, seconds) + 30)
        rc = r.returncode
    except subprocess.TimeoutExpired:
        rc = 'timeout'
    out = None
    kstats = runlog.kernel_summary(r.stdout) if rc != 'timeout' else None      # instrumentation (kstat lines)
    if rc != 'timeout' and getattr(ctx, 'stage_impr', None) is not None:      # every new best of the call, job time
        for b in runlog.kernel_stats(r.stdout).get('bests', []):
            ctx.stage_impr.append([round(t_call - ctx.T0 + b[0], 1), b[3], b[4], b[5], b[6]])
    if rc == 0 and op_.exists():
        out = core.from_kernel(op_.read_text())
        if out.value_table() != CM.AES:
            ctx.log('kernel returned a wrong function (call %d); ignored' % ctx.ncall); out = None
    else:
        ctx.log('kernel call %d exit %s: %s' % (ctx.ncall, rc, (getattr(r, 'stdout', '') or '')[-300:] if rc != 'timeout' else ''))
    ctx.rec.log.event('kernel', call=ctx.ncall, seed=seed, cap_gd=capgd, cap_a=ctx.cap['A'], cap_ad=ctx.cap['AD'],
                      repair_keep=rk, style=style, iters=iters, seconds=max(1, int(seconds)), rc=rc,
                      wall_s=round(now() - t_call, 2), start=list(m0), best=list(CM.metrics(out)) if out is not None else None,
                      lineage=list(ctx.lineage), step=getattr(ctx, 'step', None), stats=kstats)
    for p in (sp, op_, cp):
        try: p.unlink()
        except OSError: pass
    return out


def _alevels(c):
    la = [0] * c.n
    for op, a, b in c.gates:
        la.append((1 if op in core.NONLINEAR_OPS else 0) + max(la[a], la[b]))
    return la


def profile(c):
    """instrumentation: [ANDs per AND level], [linear gates per AND level] (level 0 = top, AD = bottom)"""
    la = _alevels(c); AD = max(la[o] for o in c.outputs)
    ands = [0] * (AD + 1); lin = [0] * (AD + 1)
    for j, (op, a, b) in enumerate(c.gates):
        L = min(la[c.n + j], AD)
        if op in core.NONLINEAR_OPS: ands[L] += 1
        else: lin[L] += 1
    return [ands, lin]


def and_tables(c):
    """(AND level, output table up to complement) of every AND-like gate"""
    T = c.tables(); la = _alevels(c); ones = (1 << (1 << c.n)) - 1
    return [(la[c.n + j], min(T[c.n + j], T[c.n + j] ^ ones)) for j, (op, a, b) in enumerate(c.gates) if op in core.NONLINEAR_OPS]


def _rank(vecs):
    rows = []
    for v in vecs:
        for r in rows: v = min(v, v ^ r)
        if v: rows.append(v); rows.sort(reverse=True)
    return len(rows)


def and_kept(c, ref):
    """ANDs of c whose function (up to complement) is an AND of ref"""
    sr = {t for l, t in and_tables(ref)}
    return sum(1 for l, t in and_tables(c) if t in sr)


def l1_span_kept(c, ref):
    """dimension of the level-1 AND span (modulo affine functions) that c shares with ref"""
    T = c.tables(); ones = (1 << (1 << c.n)) - 1; aff = [ones] + [T[i] for i in range(c.n)]
    f = [t for l, t in and_tables(c) if l == 1]; g = [t for l, t in and_tables(ref) if l == 1]
    ra, rf, rg, rfg = _rank(aff), _rank(aff + f), _rank(aff + g), _rank(aff + f + g)
    return (rf - ra) + (rg - ra) - (rfg - ra)


def conj_mech(start, cc, lam, k):
    """instrumentation (U3-2): profiles of the start, the naive conjugate, after BP top, the built conjugate; the
    built conjugate's ANDs kept from the naive conjugate and from the start; shared level-1 span with the start"""
    try:
        nv = LAST_BUILD.get('naive') if LAST_BUILD.get('lam') == lam and LAST_BUILD.get('k') == k else None
        d = {'profile': {'start': profile(start), 'built': profile(cc)}, 'and_kept_start': and_kept(cc, start),
             'l1_span_kept': l1_span_kept(cc, start)}
        if nv is not None:
            d['profile']['naive'] = profile(nv); d['profile']['bp_top'] = profile(LAST_BUILD['bp'])
            d['and_kept_conj'] = and_kept(cc, nv)
        return d
    except Exception as e:
        return {'mech_error': repr(e)}


def stage_mech(b, start, naive):
    try:
        d = {'profile': profile(b), 'and_kept_start': and_kept(b, start)}
        if naive is not None: d['and_kept_conj'] = and_kept(b, naive)
        return d
    except Exception as e:
        return {'mech_error': repr(e)}


def keep_circuit(out, name, c):
    """instrumentation: write circuit c (kernel text) to OUT/circuits/NAME; returns the file name (None on failure)"""
    try:
        d = Path(out) / 'circuits'; d.mkdir(exist_ok=True)
        (d / name).write_text(core.to_kernel(c)); return 'circuits/' + name
    except Exception:
        return None


def offer(ctx, c, how):
    if c is None: return
    t = CM.metrics(c)
    if CM.in_limits(t, None, ctx.lim) and not any(all(a <= b for a, b in zip(p, t)) for p in ctx.lin_front):
        ctx.lin_front = [p for p in ctx.lin_front if not all(a <= b for a, b in zip(t, p))] + [t]
        ctx.lin_changed = True                     # the lineage's own (A, AD, G, GD) set changed
    ctx.rec.offer(c, how=how, lineage=list(ctx.lineage) + [how], path_certified=ctx.cert)


def run_stage(ctx, base, mode, D, secs, seed, rk):
    """Stage loop (gate / osc / trb / mix / k) for `secs` seconds from `base` at GD cap D.
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
    ctx.stage_info = si = {'substeps': {}, 'stop': None}        # instrumentation: sub-steps by kind, why the stage ended
    if mode == 'k':
        ctx.step = 'k'
        c = kernel(ctx, base, D, None, seed, max(1, t_end - now()), rk, style='h')
        take(c, 'k%d' % D)
        si.update(substeps={'k': 1}, stop='single kernel run')
        return best
    while t_end - now() > 2:
        sub += 1
        rem = t_end - now()
        kseed = seed * 100000 + sub
        m = mode
        if m == 'm': m = ['g', 'o', 't'][sub % 3]
        ctx.step = '%s%d' % (m, sub); si['substeps'][m] = si['substeps'].get(m, 0) + 1
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
    si['stop'] = 'stage time (%.0f s left of the job)' % left()
    return best


def is_conjugated(path, depth=0):
    """True if the start's sidecar (or its parent chain, up to 6 links) records a GF(2^8) conjugation:
    a conjpull lineage 'conj lam ..', or a conjugate file name/method of older records (cj-, conj, mkconj)."""
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
    ap.add_argument('--beam-rk', default='', help='repair_keep per beam seed, e.g. 0,1 (a matched comparison)')
    ap.add_argument('--cap-a', type=int, default=None, help='search A cap below the target A (kernel cap.a, stage choice)')
    ap.add_argument('--cap-ad', type=int, default=None, help='search AD cap below the target AD (e.g. 4 for an AD5 reference)')
    ap.add_argument('--stall-stages', type=int, default=2,
                    help='drop the lineage (go to the next conjugate) after N consecutive stages that recorded no '
                         'new point; 0 = off')
    ap.add_argument('--allow-reconj', action='store_true', help='conjugate a start whose sidecar lineage is a conjugate')
    ap.add_argument('--kcfg', nargs='*', default=[])
    ap.add_argument('--stage-iters', type=int, default=200000)
    ap.add_argument('--relax', type=int, default=1)
    ap.add_argument('--repair-iters', type=int, default=100000)
    ap.add_argument('--trb-regions', default='bottom,top,mid,random')
    ap.add_argument('--top-runs', type=int, default=12, help='BP runs when building a conjugate (mkconj)')
    ap.add_argument('--screen-runs', type=int, default=4, help='BP runs per conjugate in the conj3 screen')
    ap.add_argument('--screen-cache', default=str(CM.CACHE / 'cache' / 'conj3'))
    ap.add_argument('--kernel', default=None, help='kernel binary (default: repo build bfx-<sha1(bfx.c)[:10]>)')
    a = ap.parse_args(argv)
    function = CM.init_function(a)
    T0 = now(); T_END = T0 + a.seconds
    a.repair_keep = a.seed % 2 if str(a.repair_keep) == 'alt' else int(a.repair_keep)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    logf = open(out / 'conjpull.log', 'a')
    def log(*x):
        logf.write('%s %7.1f %s\n' % (time.strftime('%H:%M:%S', time.gmtime()), now() - T0, ' '.join(map(str, x)))); logf.flush()
    ctx = Ctx(); ctx.a = a; ctx.log = log; ctx.ncall = 0; ctx.T0 = T0; ctx.stage_impr = []
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
              'caps': {'A': ctx.lim['A'], 'AD': ctx.lim['AD']}, 'kernel_bin': ctx.bfx.name, 'function': function}
    command = ' '.join([sys.executable, str(Path(__file__).resolve())] + list(argv if argv is not None else sys.argv[1:]))
    method = (('' if function == 'aes-sbox' else '%s: ' % CM.aesfn.label(function)) +
              'ops/conjpull.py: GF(2^8) conjugate (conj3 screen + build_conj) then staged kernel pulls %s '
              '(kernel %s, repair_keep %d unless a stage says rk0/rk1); search states may exceed '
              'caps, recorded circuits inside A<=%d AD<=%d' % (a.schedule, ctx.bfx.name, a.repair_keep, ctx.lim['A'], ctx.lim['AD']))
    rec = CM.Recorder(out, OP, a.target, a.inp, a.seed, command, method, params, kernel=ctx.bfx, t0=T0,
                      budget_s=a.seconds,
                      seeds={'stage_seed': 'seed x 1000 + stage index x 10 + beam index (or the stage s<N> option); '
                                            'every stage and kernel seed is an event in events.jsonl.gz',
                             'kernel_seed': 'stage seed x 100000 + sub-step (+7, +13 within an osc step)',
                             'trb_rng': 'random.Random(stage seed)'})
    ctx.rec = rec; a._rec = rec                       # a._rec: conj_list's screen event
    stages_log = []

    def on_alarm(sig, frm):
        try:                                  # instrumentation: which signal ended the job, and when
            nm = signal.Signals(sig).name
            rec.log.event('signal', signal=sig, name=nm, elapsed_s=round(now() - T0, 1), left_s=round(left(), 1))
            rec.notes.append('ended by %s at %.1f s' % (nm, now() - T0))
        except Exception:
            pass
        rec.finish('timeout', {'stages': stages_log})
        os._exit(3)
    signal.signal(signal.SIGALRM, on_alarm); signal.alarm(int(a.seconds + 45))
    signal.signal(signal.SIGTERM, on_alarm)

    status = 'ok'; items_all = []; fates_all = {}; skipped_all = []
    budget_need = sum(x[2] for x in sched)
    try:
        start = CM.load(a.inp)
        assert start.value_table() == CM.AES, 'start does not compute the %s' % CM.aesfn.label(function)
        log('start', CM.metrics(start), a.inp, 'kernel', ctx.bfx)
        items = conj_list(a.conj, start, rec.start_sha, a, log); items_all[:] = items
        skipped_conj = []
        if is_conjugated(a.inp) and not a.allow_reconj:
            skipped = [x[0] for x in items if x[1] is not None]; skipped_conj = list(skipped); skipped_all[:] = skipped
            items = [x for x in items if x[1] is None]
            if skipped:
                rec.notes.append('start is already a conjugate (sidecar lineage); conjugates %s skipped (a conjugate '
                                 'is not conjugated again; --allow-reconj overrides)%s' % (skipped, '' if items else '; identity pull instead'))
                log(rec.notes[-1])
            if not items:
                items = [('id', None, None, None)]
        if budget_need * max(1, sum(1 for x in items if x[1] is not None)) > a.seconds:
            rec.notes.append('schedule %.0f s x %d conjugates > --seconds %.0f: later conjugates will not be reached' % (
                budget_need, sum(1 for x in items if x[1] is not None), a.seconds)); log(rec.notes[-1])
        rec.log.event('items', items=[list(x) for x in items], n=len(items))     # instrumentation: the conjugates chosen, in order
        fates = fates_all
        for ii, (name, lam, k, score) in enumerate(items):
            if left() < 30:
                for x in items[ii:]: fates[x[0]] = 'skipped: less than 30 s left'
                rec.log.event('stop', what='conjugate loop', reason='less than 30 s left', done=ii, of=len(items)); break
            ctx.cert = True; ctx.lin_front = []; ctx.lin_changed = False; quiet = 0; fates[name] = 'run: 0 stages'
            if lam is None:
                cc = start; ctx.lineage = ['start']
            else:
                t1 = now()
                cc = build_conj(start, lam, k, a.top_runs)
                rec.log.event('conjugate', name=name, lam=lam, k=k, score=score, metrics=list(CM.metrics(cc)),
                              build_rng='random.Random(%d) (BP top), random.Random(1) (resynth)' % (lam * 8 + k),
                              build_s=round(now() - t1, 2), start_metrics=list(CM.metrics(start)),
                              n_tied=sum(1 for r in (getattr(a, '_rows', None) or []) if score is not None and r['sum'] == score),
                              n_within1=sum(1 for r in (getattr(a, '_rows', None) or []) if score is not None and r['sum'] <= score + 1),
                              file=keep_circuit(out, 'conj-%d-%d.bfx' % (lam, k), cc), **conj_mech(start, cc, lam, k))
                ctx.lineage = ['conj lam %d k %d (%s, score %s)' % (lam, k, name, score)]
                log('conjugate', name, lam, k, 'score', score, '->', CM.metrics(cc), '%.1fs' % (now() - t1))
            cur = cc
            ctx.lin_front = [CM.metrics(cc)]          # the lineage's own set starts at its input (not recorded)
            for si, (mode, cap, secs, rk, sseed) in enumerate(sched):
                if left() < 20:
                    rec.log.event('stop', what='stage loop', conj=name, reason='less than 20 s left', stage=si + 1); break
                if a.stall_stages and quiet >= a.stall_stages:
                    log('lineage dropped: %d stages without a change in its (A, AD, G, GD) set' % quiet)
                    rec.log.event('stop', what='stage loop', conj=name, reason='lineage dropped: %d stages without a change in '
                                  'its (A, AD, G, GD) set (--stall-stages %d)' % (quiet, a.stall_stages), stage=si + 1,
                                  lineage_front=[list(p) for p in ctx.lin_front])
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
                    t1 = now(); nw0 = len(rec.points); nk0 = ctx.ncall; bud = min(secs, left() - 15); ctx.stage_impr = []
                    b = run_stage(ctx, cur, mode, D, bud, sd, rkk)
                    ctx.lineage.pop()
                    bests.append(b)
                    stages_log.append({'conj': name, 'lam': lam, 'k': k, 'stage': si + 1, 'mode': mode, 'cap': D,
                                       'seed': sd, 'in': list(CM.metrics(cur)), 'best': list(CM.metrics(b)),
                                       'seconds': round(now() - t1, 1), 'repair_keep': rkk,
                                       'improvements': list(ctx.stage_impr)})      # [job s, A, AD, G, GD] of every kernel best
                    si_ = getattr(ctx, 'stage_info', None) or {}
                    sbf = keep_circuit(out, 'stage-%s-%d-%d-best.bfx' % (name.replace(':', '_'), si + 1, j), b)
                    rec.log.event('stage', **stages_log[-1], budget_s=round(bud, 1),
                                  written=len(rec.points) - nw0, kernel_calls=ctx.ncall - nk0, lineage_changed=ctx.lin_changed,
                                  substeps=si_.get('substeps'), stop=si_.get('stop'), file=sbf,
                                  **stage_mech(b, start, LAST_BUILD.get('naive') if lam is not None and LAST_BUILD.get('lam') == lam and LAST_BUILD.get('k') == k else None))
                    log('stage', si + 1, mode, D, 'seed', sd, CM.metrics(cur), '->', CM.metrics(b), '%.0fs' % (now() - t1))
                feasD = lambda c: CM.metrics(c)[3] <= D
                bests.sort(key=lambda c: (0 if feasD(c) else 1, CM.metrics(c)[2], CM.metrics(c)[3]))
                if bests:
                    nxt = bests[0]
                    ctx.lineage.append('stage %d %s:%d best %s' % (si + 1, mode, D, '/'.join(map(str, CM.metrics(nxt)))))
                    cur = nxt
                quiet = 0 if ctx.lin_changed else quiet + 1
                fates[name] = 'run: %d stages' % (si + 1)
                rec.write_result({'stages': stages_log})
        rec.log.event('item-fates', fates=fates, skipped_conjugated=skipped_conj)
    except Exception as e:
        import traceback
        status = 'error'; rec.notes.append(traceback.format_exc()[-1500:]); log('ERROR', repr(e))
    signal.alarm(0)
    planned = [x[0] for x in items_all] if items_all else None
    run_ = [{'label': x[0], 'lam': x[1], 'k': x[2], 'screen_score': x[3],
             'screen_rank': int(x[0][5:]) if str(x[0]).startswith('rank:') else None,
             'stages_done': sum(1 for st in stages_log if st.get('conj') == x[0] and 'stage' in st),
             'stages_planned': len(sched), 'seconds': round(sum(st.get('seconds', 0) for st in stages_log if st.get('conj') == x[0]), 1)}
            for x in (items_all or []) if x[0] in fates_all and fates_all[x[0]].startswith('run')]
    rec.finish(status, {'stages': stages_log, 'kernel_calls': ctx.ncall, 'conj_planned': planned, 'conj_run': run_,
                        'conj_not_reached': [x for x in (planned or []) if not fates_all.get(x, '').startswith('run')],
                        'conj_replaced': [{'label': x, 'reason': 'start is already a conjugate'} for x in skipped_all]})
    log('end', status, 'written', len(rec.points), 'pareto', [p['tuple'] for p in rec.best_points()['pareto_G_GD']])
    return 0 if status == 'ok' else 1


if __name__ == '__main__':
    sys.exit(main())
