#!/usr/bin/env python3
"""conjpull: GF(2^8) conjugate + staged kernel pull operator (library: ops/conj_lib/).

    python3 search/nonlinear/boolflux/ops/conjpull.py --in START --target REF --seed S \
        --seconds T --out DIR [--cpus 1]
        [--conj ITEMS]            comma list, processed in order until the time ends:
                                    id            the start itself (no conjugation)
                                    L:K           conjugate lam L, k K (x -> L x^(2^K))
                                    rank:R        the R-th best non-identity conjugate by the conj3 score
                                    top:N         ranks 1..N;   all = all 2039 non-identity, by score
                                    sh:K          successive halving: K conjugates (188:0, 189:0, the k=0/4
                                                  conjugates that keep the start's whole level-1 AND span
                                                  (--sh-span), then the screen order) each run the FIRST stage
                                                  of the schedule; the best --sh-keep by (A, AD, G + max(0,
                                                  GD - d), GD) after it run the remaining stages (d = start GD)
                                  default rank:1
        [--schedule STAGES]       comma list MODE:CAP:SECONDS[:rk0|rk1]; default g:31:200,m:27:200,m:25:200
                                    g gate (kernel restarted from the stage best)
                                    m mix (gate / osc / trb rotation)   o osc   t trb
                                    k one hub-style kernel run, objective cost,gd
                                  CAP: N absolute; +N / -N relative to the GD of the stage's input; d, d+N, d-N
                                  relative to the start's GD.  --caps plan (default): as written.  --caps lineage
                                  (opt-in; not shown better in the 2026-11-17 A/B): from the second stage on, an N or
                                  d+N cap is D = max(in - P, min(planned, in - 1)) (in = the stage input's GD,
                                  P = --max-pull, default 2, 0 = no floor): every later stage pulls, by at most P
        [--missed-pulls N]        drop the lineage after N consecutive stages that pulled and ended above their cap
                                  (default 0 = off)
        [--stage-choice old|4d]   stage best: feasible at the cap, then G, GD (old, default) or A, AD, G, GD with the
                                  kernel's intermediate bests and Pareto beam starts (4d)
        [--stall-stages N]        drop it after N consecutive stages that recorded no new point (default 2)
        [--overrun scale|refuse]  when the plan (items x schedule seconds) exceeds --seconds: scale every stage of
                                  the not yet started items (default; a note and a `plan` event), or refuse the job
                                  (status refused).  Each item's stages get the time left / the remaining plan
        [--identity-first auto|yes|no]  default no.  auto: an identity staged pull (dropped after one stage without a new point)
                                  before screen-chosen conjugates (rank/top/all/sh) when the start is not a BoolFlux
                                  output (no sidecar with an op, e.g. a NIST seed) and the registry has no identity
                                  pull of it
        [--registry FILE]         (default $BOOLFLUX_CONJ_REGISTRY; off when unset) campaign registry: an item whose
                                  (start sha256, lam, k, schedule) is in it is skipped (sh: the next screen rank
                                  is taken); every started item is appended
        [--allow-reconj]          conjugate a start that is itself a conjugate (sidecar lineage / file header);
                                  without it conjugates of such a start are refused (status refused when nothing
                                  else is left), never replaced by an identity pull
        [--keep-bests N]          offer the kernel's intermediate bests too (cleaned 4-D Pareto set, at most N per
                                  kernel call; default 8, 0 = off)
        [--bp-cap none|N|d+N]     GD cap of the Boyar-Peralta top of build_conj (default none = 99, as before;
                                  with a cap the best run meeting it, else the best run)
        [--beam B]                seeds per stage (sequential on this CPU), all from the stage input (with
                                  --stage-choice 4d: seed j from the j-th member of the previous stage's Pareto set);
                                  the stage best (see --stage-choice) goes on; default 1
        [--repair-keep 0|1]       kernel repair_keep for every stage without its own rk flag; default 1
        [--kcfg KEY=VAL ...]      extra kernel settings (e.g. T0=0.8 stall_it=80000)
        [--stage-iters N] [--relax R] [--repair-iters N] [--trb-regions LIST] [--top-runs N]
        [--screen-cache DIR]      conj3 screen cache (shared, per start sha256); default $BOOLFLUX_CACHE/cache/conj3

Search states may exceed the A, AD, G and GD caps: the stage caps are
kernel caps on GD only plus the target's A/AD as kernel caps, the stage input may be above them
(repair), and only RECORDED circuits must be inside A <= ref A, AD <= ref AD (common.Recorder).  Every
kernel output, the kernel's intermediate bests, osc-relaxed state and trb rebuild inside the hard limits is
offered to the recorder, which writes each new job-local Pareto point (aes_check, sidecar) at once.

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
import re
import shutil
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
RESERVE_S = 20.0          # seconds of the job kept free of stages (builds, result writing)
SPAN_KEEPERS_ALWAYS = [(188, 0), (189, 0)]       # GF(4) scalars: keep the whole level-1 span on every start seen (U3)


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
    and output map Out are conj.maps() of the process's function (aes-sbox: G and Mout).  A top cost of
    0 counts as 0 (before 2026-11-17 `ct or 99` made it 99; no conjugate of a NIST circuit has one)."""
    import conj3 as C3
    CJ = C3.CJ
    top, outs, nl = C3.layers(c)
    rows = []
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
        rows.append({'lam': lam, 'k': k, 'top': ct, 'bot': cb, 'sum': (99 if ct is None else ct) + cb})
    return rows


LAST_BUILD = {}           # instrumentation: the intermediate circuits of the last build_conj (naive, BP top)


def build_conj(c, lam, k, top_runs=12, bp_cap=None):
    """Naive conjugate circuit, BP top resynthesis (GD cap bp_cap: the best run meeting it, else the best
    run; None = no cap, as before 2026-11-17), trb top/bottom passes; verified."""
    import conj as CJ
    import bp
    cc = CJ.conj_circuit(c, lam, k)
    LAST_BUILD.clear(); LAST_BUILD.update(lam=lam, k=k, naive=cc)
    if bp_cap is None:
        best, info = bp.optimise(cc, 99, 'top', random.Random(lam * 8 + k), top_runs, log=lambda *x: None)
    else:
        # depth-aware variant: the naive output chains first go through one trb bottom pass (else the circuit's GD
        # is above any useful cap whatever the top), then the BP run with the fewest gates among those with GD <= cap
        import trb
        cb, _ = trb.rebuild(cc, cc.metrics(CJ.MODEL)['GD'], 'bottom', random.Random(1))
        if cb.value_table() == CM.AES and len(cb.gates) <= len(cc.gates): cc = cb
        best, info = bp.optimise(cc, bp_cap, 'top', random.Random(lam * 8 + k), top_runs, log=lambda *x: None,
                                 fallback=True)
    LAST_BUILD['bp_fallback'] = bool(info.get('fallback'))
    if best is not None: cc = best
    LAST_BUILD['bp'] = cc
    cc = CJ.resynth(cc, random.Random(1), 2)
    assert cc.value_table() == CM.AES, 'conjugate %d:%d wrong function' % (lam, k)
    return cc


def span_keepers(start, ks=(0, 4)):
    """(lam, k) with k in ks whose naive conjugate keeps the start's whole level-1 AND span (modulo affine
    functions): the conjugates that re-coordinatise the first AND layer (U3: 188:0, 189:0 on every start
    seen, some k=4 ones on AD5 tower circuits)"""
    import conj as CJ
    T = start.tables(); ones = (1 << (1 << start.n)) - 1; aff = [ones] + [T[i] for i in range(start.n)]
    full = _rank(aff + [t for l, t in and_tables(start) if l == 1]) - _rank(aff)
    out = []
    for k in ks:
        for lam in range(1, 256):
            if (lam, k) == (1, 0): continue
            try:
                if l1_span_kept(CJ.conj_circuit(start, lam, k), start) == full: out.append((lam, k))
            except Exception:
                pass
    return out, full


def conj_list(spec, c, start_sha, a, log):
    """Items of --conj in order: ('id', None, None, None), (label, lam, k, screen score) or ('sh:K', 'sh', K, None)
    (successive halving, candidates in a._sh_cands)."""
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
        elif it.startswith('sh:'):
            K = int(it[3:]); assert K >= 1, 'sh:K needs K >= 1'
            rs = get_rows()
            rank = {(r['lam'], r['k']): (i + 1, r['sum']) for i, r in enumerate(rs)}
            t1 = now(); keepers, full = span_keepers(c) if a.sh_span else ([], None)
            extra = list(SPAN_KEEPERS_ALWAYS) + sorted((x for x in keepers if x[1] != 0 and x not in SPAN_KEEPERS_ALWAYS),
                                                       key=lambda x: rank.get(x, (9999,))[0])[:a.sh_span]
            cands = []
            for lam, k in extra:
                if (lam, k) not in [(x[1], x[2]) for x in cands]:
                    cands.append(('%d:%d' % (lam, k), lam, k, rank.get((lam, k), (None, None))[1]))
            for i, r in enumerate(rs):                   # the screen order after them; the registry may skip some
                if (r['lam'], r['k']) not in [(x[1], x[2]) for x in cands]:
                    cands.append(('rank:%d' % (i + 1), r['lam'], r['k'], r['sum']))
            a._sh_cands = cands; a._sh_K = K; a._sh_extra = len([x for x in extra])
            a._sh_info = {'span_keepers': [list(x) for x in keepers], 'level1_span_dim': full,
                          'span_s': round(now() - t1, 2), 'extra': [list(x) for x in extra]}
            items.append(('sh:%d' % K, 'sh', K, None))
        else:
            lam, k = map(int, it.split(':'))
            items.append(('%d:%d' % (lam, k), lam, k, None))
    return items


# ---- campaign registry (never repeat start, conjugate, schedule) ------------------------------------

def reg_key(sha, lam, k, sched_spec):
    return json.dumps([sha, lam, k, sched_spec])


def reg_load(path):
    if not path or not Path(path).exists(): return {}
    out = {}
    for ln in Path(path).read_text().splitlines():
        try:
            e = json.loads(ln); out[reg_key(e['start_sha256'], e['lam'], e['k'], e['schedule'])] = e
        except Exception:
            continue
    return out


def reg_add(path, entry):
    if not path: return
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'a') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.write(json.dumps(entry) + '\n'); f.flush()
        fcntl.flock(f, fcntl.LOCK_UN)


# ---- kernel stages (in-process) ------------------------------------------------------------------

class Ctx:
    pass


class Lineage:
    """One staged pull: a conjugate (or the start) and its stage results."""
    def __init__(self, name, lam, k, score, cc, label, stall, naive=None, screen_rank=None):
        self.name, self.lam, self.k, self.score = name, lam, k, score
        self.cur = cc; self.lineage = [label]; self.cert = True
        self.lin_front = [CM.metrics(cc)]          # the lineage's own set starts at its input (not recorded)
        self.quiet = 0; self.missed = 0; self.stall = stall; self.naive = naive
        self.pareto = []; self.stages_done = 0; self.dropped = None; self.screen_rank = screen_rank
        self.seconds = 0.0; self.s1 = None; self.halving_rank = None


def pareto_circuits(cs, cap=None):
    """4-D (A, AD, G, GD) Pareto set of circuits (first of equal tuples), sorted by tuple; at most cap"""
    by = {}
    for c in cs:
        by.setdefault(tuple(CM.metrics(c)), c)
    keys = [t for t in by if not any(CM.dominates(o, t) for o in by)]
    keys.sort()
    if cap is not None: keys = keys[:cap]
    return [by[t] for t in keys]


def kernel(ctx, c, capgd, iters, seed, seconds, rk, style='f'):
    """One kernel call; returns (the kernel's best circuit (checked to compute the S-box) or None, the cleaned
    4-D Pareto set of its intermediate bests (keep_bests; at most --keep-bests, the final excluded))."""
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
    kd = ctx.wd / (tag + '.bests')
    sp.write_text(core.to_kernel(c))
    cfg.update({'in': sp, 'out': op_, 'seed': seed, 'seconds': max(1, int(seconds))})
    if ctx.a.keep_bests:
        kd.mkdir(exist_ok=True); cfg['keep_bests'] = kd
    if iters: cfg['iters'] = iters
    cp.write_text(''.join('%s %s\n' % kv for kv in cfg.items()))
    m0 = CM.metrics(c)
    inside = m0[0] <= ctx.cap['A'] and m0[1] <= ctx.cap['AD'] and m0[3] <= capgd
    ctx.L.cert = ctx.L.cert and (inside or rk == 1)
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
    inter = []; n_files = 0
    if ctx.a.keep_bests and kd.exists():
        fs = sorted(kd.glob('best-*.bfx'), key=lambda p: int(p.stem.split('-')[1]))
        n_files = len(fs)
        fin = core.to_kernel(out) if out is not None else None
        for p in fs:
            try:
                x = core.from_kernel(p.read_text())
            except Exception:
                continue
            if fin is not None and core.to_kernel(x) == fin: continue
            if x.value_table() != CM.AES: continue
            inter.append(clean(x))
        inter = pareto_circuits(inter)
        if len(inter) > ctx.a.keep_bests:                # the latest ones (closest to the final)
            inter = sorted(inter, key=lambda x: CM.metrics(x)[2])[:ctx.a.keep_bests]
        shutil.rmtree(kd, ignore_errors=True)
    ctx.rec.log.event('kernel', call=ctx.ncall, seed=seed, cap_gd=capgd, cap_a=ctx.cap['A'], cap_ad=ctx.cap['AD'],
                      repair_keep=rk, style=style, iters=iters, seconds=max(1, int(seconds)), rc=rc,
                      wall_s=round(now() - t_call, 2), start=list(m0), best=list(CM.metrics(out)) if out is not None else None,
                      lineage=list(ctx.L.lineage), step=getattr(ctx, 'step', None), stats=kstats,
                      bests_files=n_files, bests_offered=[list(CM.metrics(x)) for x in inter])
    for p in (sp, op_, cp):
        try: p.unlink()
        except OSError: pass
    return out, inter


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
            d['and_kept_conj'] = and_kept(cc, nv); d['bp_fallback'] = LAST_BUILD.get('bp_fallback')
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
    L = ctx.L
    t = CM.metrics(c)
    if CM.in_limits(t, None, ctx.lim) and not any(all(a <= b for a, b in zip(p, t)) for p in L.lin_front):
        L.lin_front = [p for p in L.lin_front if not all(a <= b for a, b in zip(t, p))] + [t]
        ctx.lin_changed = True                     # the lineage's own (A, AD, G, GD) set changed
    ctx.rec.offer(c, how=how, lineage=list(L.lineage) + [how], path_certified=L.cert)


def run_stage(ctx, base, mode, D, secs, seed, rk):
    """Stage loop (gate / osc / trb / mix / k) for `secs` seconds from `base` at GD cap D.
    Returns (the stage best: hard-limit circuits only; feasible at D first, then G, GD (default, as before
    2026-11-17) or A, AD, G, GD (--stage-choice 4d); the 4-D Pareto set (at most 8) of the hard-limit circuits of
    the stage).  The kernel's intermediate bests are always offered to the recorder; only with --stage-choice 4d
    do they take part in the stage choice."""
    lim = ctx.cap                     # search caps (default = target limits; --cap-a / --cap-ad tighter)
    met = CM.metrics
    hard = lambda c: met(c)[0] <= lim['A'] and met(c)[1] <= lim['AD']
    feas = lambda c: hard(c) and met(c)[3] <= D
    four = ctx.a.stage_choice == '4d'
    key = (lambda c: (0 if feas(c) else 1,) + tuple(met(c))) if four else (lambda c: (0 if feas(c) else 1, met(c)[2], met(c)[3]))
    rng = random.Random(seed)
    t_end = min(now() + secs, T_END - 15)
    best = base; cur = base
    seen = []
    def take(c, how, inter=()):
        nonlocal best
        for x in inter:              # the kernel's intermediate bests (already cleaned and verified)
            offer(ctx, x, how + '-kb')
            if four and hard(x):
                seen.append(x)
                if key(x) < key(best): best = x
        if c is None: return
        c = clean(c)                  # structural-hash merge of duplicate gates (function unchanged)
        offer(ctx, c, how)
        if hard(c):
            seen.append(c)
            if key(c) < key(best): best = c
    sub = 0
    ctx.stage_info = si = {'substeps': {}, 'stop': None}        # instrumentation: sub-steps by kind, why the stage ended
    if mode == 'k':
        ctx.step = 'k'
        c, inter = kernel(ctx, base, D, None, seed, max(1, t_end - now()), rk, style='h')
        take(c, 'k%d' % D, inter)
        si.update(substeps={'k': 1}, stop='single kernel run')
        return best, pareto_circuits(seen, 8)
    while t_end - now() > 2:
        sub += 1
        rem = t_end - now()
        kseed = seed * 100000 + sub
        m = mode
        if m == 'm': m = ['g', 'o', 't'][sub % 3]
        ctx.step = '%s%d' % (m, sub); si['substeps'][m] = si['substeps'].get(m, 0) + 1
        b = best if feas(best) else cur
        if m == 'g':
            c, inter = kernel(ctx, b, D, ctx.a.stage_iters, kseed, rem, rk)
            take(c, 'g%d' % D, inter)
            if c is not None and hard(c): cur = c
        elif m == 'o':
            c1, inter = kernel(ctx, b, D + ctx.a.relax, ctx.a.stage_iters // 2, kseed, rem / 2, rk)
            take(c1, 'o%d-relaxed%d' % (D, D + ctx.a.relax), inter)
            if c1 is None: continue
            c2, inter = kernel(ctx, c1, D, ctx.a.repair_iters, kseed + 7, max(1, t_end - now()), rk)
            take(c2, 'o%d-repair' % D, inter)
            if c2 is not None and feas(c2) and t_end - now() > 2:
                c3, inter = kernel(ctx, c2, D, ctx.a.stage_iters // 2, kseed + 13, max(1, t_end - now()), rk)
                take(c3, 'o%d-gate' % D, inter)
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
            c2, inter = kernel(ctx, c1, D, ctx.a.stage_iters, kseed, max(1, t_end - now()), rk)
            take(c2, 't%d-%s' % (D, reg), inter)
            if c2 is not None and hard(c2): cur = c2
    si['stop'] = 'stage time (%.0f s left of the job)' % left()
    return best, pareto_circuits(seen, 8)


def _sidecar(p):
    p = Path(p); name = p.name
    stem = name[:-len('.circ.txt')] if name.endswith('.circ.txt') else p.stem
    return p.with_name(stem + '.json')


CONJ_TEXT = re.compile(r'conj lam \d+|conjugate lam|conj\.py of|mkconj|conj(ugate)? \(?lam')


def is_conjugated(path, depth=0):
    """True if the start is a GF(2^8) conjugate, by content, never by its path: the circuit file's comment
    lines name a conjugate (conj.py / mkconj / 'conj lam L k K'), or its sidecar's lineage does (a conjpull
    record: 'conj lam ..'; an identity pull of conjpull has lineage 'start' and is NOT a conjugate), or, for a
    record of another method, its method text does; else the same for its parent (up to 6 links)."""
    p = Path(path)
    try:
        head = [l for l in p.read_text().splitlines()[:60] if l.lstrip().startswith(('%', '#'))]
    except Exception:
        head = []
    if any(CONJ_TEXT.search(l) for l in head):
        return True
    j = _sidecar(p)
    if not j.exists() or depth > 6: return False
    try: m = json.loads(j.read_text())
    except Exception: return False
    if CONJ_TEXT.search(json.dumps(m.get('lineage') or '')):
        return True
    if m.get('op') != OP:                 # conjpull's method text names conjugation for identity pulls too
        meth = json.dumps(m.get('method') or '').lower()
        if CONJ_TEXT.search(meth) or 'conjugate (' in meth:
            return True
    par = (m.get('parent') or m.get('start') or {})
    par = par.get('path') if isinstance(par, dict) else par
    return bool(par) and Path(par).exists() and Path(par).resolve() != p.resolve() and is_conjugated(par, depth + 1)


def is_boolflux_output(path):
    """the start was written by BoolFlux (first line 'written by .../boolflux', or a sidecar of a BoolFlux
    method or the hub: an 'op' or 'run' field): already kernel-polished; NIST seeds have neither"""
    try:
        first = Path(path).read_text().split('\n', 1)[0]
    except Exception:
        first = ''
    if 'written by' in first and 'boolflux' in first: return True
    j = _sidecar(path)
    if not j.exists(): return False
    try: m = json.loads(j.read_text())
    except Exception: return False
    return bool(m.get('op') or m.get('run'))


CAP_RE = re.compile(r'^([+-]\d+|d([+-]\d+)?|\d+)$')


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
        assert CAP_RE.match(cap), 'stage cap %r: N, +N, -N, d, d+N or d-N' % cap
        st.append((mode, cap, secs, rk, seed))
    return st


def stage_cap(cap, gd_in, d0, si, lineage_caps, max_pull=2):
    """GD cap of stage si (0-based) for an input of GD gd_in; d0 = the start's GD.  Returns (D, planned).
    lineage_caps: from the second stage on D = min(planned, gd_in - 1), and at most max_pull levels below gd_in
    (max_pull 0: no floor)."""
    if cap[0] in '+-':
        D = gd_in + int(cap); return D, D
    planned = d0 + int(cap[1:] or 0) if cap[0] == 'd' else int(cap)
    D = planned
    if lineage_caps and si > 0:
        D = min(planned, gd_in - 1)
        if max_pull > 0: D = max(gd_in - max_pull, D)
    return D, planned


def sched_spec(sched, idx):
    return ','.join('%s:%s:%g' % (m, c, s) + (':rk%d' % rk if rk is not None else '') for (m, c, s, rk, sd) in
                    (sched[i] for i in idx))


def main(argv=None):
    global T_END
    ap = CM.contract_args(argparse.ArgumentParser(description=__doc__.split('\n')[0]))
    ap.add_argument('--conj', default='rank:1')
    ap.add_argument('--schedule', default='g:31:200,m:27:200,m:25:200')
    ap.add_argument('--beam', type=int, default=1)
    ap.add_argument('--repair-keep', type=int, choices=(0, 1), default=1,
                    help='kernel repair_keep of stages without an rk flag (default 1; the seed-parity alt split and '
                         '--beam-rk were removed 2026-11-17: no visible effect, U3)')
    ap.add_argument('--cap-a', type=int, default=None, help='search A cap below the target A (kernel cap.a, stage choice)')
    ap.add_argument('--cap-ad', type=int, default=None, help='search AD cap below the target AD (e.g. 4 for an AD5 reference)')
    ap.add_argument('--stall-stages', type=int, default=2,
                    help='drop the lineage (go to the next conjugate) after N consecutive stages that recorded no '
                         'new point; 0 = off')
    ap.add_argument('--missed-pulls', type=int, default=0,
                    help='drop the lineage after N consecutive pulls that ended above their cap; 0 = off (default)')
    ap.add_argument('--stage-choice', choices=('old', '4d'), default='old',
                    help='old (default): stage best = feasible at the cap, then G, GD; 4d: then A, AD, G, GD, the '
                         "kernel's intermediate bests included, beam seeds from the stage's Pareto set")
    ap.add_argument('--caps', choices=('lineage', 'plan'), default='plan',
                    help='lineage: from stage 2 on, absolute and d-relative caps become max(in-2, min(planned, in-1)); '
                         'plan: as written (before 2026-11-17)')
    ap.add_argument('--max-pull', type=int, default=2,
                    help='--caps lineage: a later stage cap at most N levels below its input GD (0 = no floor)')
    ap.add_argument('--overrun', choices=('scale', 'refuse'), default='scale')
    ap.add_argument('--identity-first', choices=('auto', 'yes', 'no'), default='no')
    ap.add_argument('--registry', default=os.environ.get('BOOLFLUX_CONJ_REGISTRY') or None)
    ap.add_argument('--sh-keep', type=int, default=2, help='sh:K: lineages continued after the first stage')
    ap.add_argument('--sh-span', type=int, default=2,
                    help='sh:K: k=4 span-keeping conjugates added after 188:0 and 189:0 (by screen rank); 0 = none')
    ap.add_argument('--keep-bests', type=int, default=8)
    ap.add_argument('--bp-cap', default='none', help='none, N, or d+N (start GD + N): GD cap of build_conj BP top')
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
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    logf = open(out / 'conjpull.log', 'a')
    def log(*x):
        logf.write('%s %7.1f %s\n' % (time.strftime('%H:%M:%S', time.gmtime()), now() - T0, ' '.join(map(str, x)))); logf.flush()
    ctx = Ctx(); ctx.a = a; ctx.log = log; ctx.ncall = 0; ctx.T0 = T0; ctx.stage_impr = []; ctx.lin_changed = False
    ctx.L = None                                       # the lineage being run (Lineage)
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
    sched = parse_schedule(a.schedule); ctx.sched = sched
    params = {'conj': a.conj, 'schedule': a.schedule, 'beam': a.beam, 'repair_keep': a.repair_keep,
              'kcfg': ctx.kcfg, 'stage_iters': a.stage_iters, 'relax': a.relax, 'repair_iters': a.repair_iters,
              'trb_regions': a.trb_regions, 'top_runs': a.top_runs, 'screen_runs': a.screen_runs,
              'caps': {'A': ctx.lim['A'], 'AD': ctx.lim['AD']}, 'kernel_bin': ctx.bfx.name, 'function': function,
              'stage_caps': a.caps, 'stage_choice': a.stage_choice, 'max_pull': a.max_pull, 'missed_pulls': a.missed_pulls, 'stall_stages': a.stall_stages, 'overrun': a.overrun,
              'identity_first': a.identity_first, 'registry': a.registry, 'sh_keep': a.sh_keep, 'sh_span': a.sh_span,
              'keep_bests': a.keep_bests, 'bp_cap': a.bp_cap}
    command = ' '.join([sys.executable, str(Path(__file__).resolve())] + list(argv if argv is not None else sys.argv[1:]))
    method = (('' if function == 'aes-sbox' else '%s: ' % CM.aesfn.label(function)) +
              'ops/conjpull.py: staged kernel pulls %s of a GF(2^8) conjugate (conj3 screen + build_conj) or of the '
              'start itself (identity pull; the sidecar lineage says which) (kernel %s, repair_keep %d unless a stage '
              'says rk0/rk1); search states may exceed caps, recorded circuits inside A<=%d AD<=%d' % (
                  a.schedule, ctx.bfx.name, a.repair_keep, ctx.lim['A'], ctx.lim['AD']))
    rec = CM.Recorder(out, OP, a.target, a.inp, a.seed, command, method, params, kernel=ctx.bfx, t0=T0,
                      budget_s=a.seconds,
                      seeds={'stage_seed': 'seed x 1000 + stage index x 10 + beam index (or the stage s<N> option); '
                                            'every stage and kernel seed is an event in events.jsonl.gz',
                             'kernel_seed': 'stage seed x 100000 + sub-step (+7, +13 within an osc step)',
                             'trb_rng': 'random.Random(stage seed)'})
    ctx.rec = rec; a._rec = rec                       # a._rec: conj_list's screen event
    stages_log = []
    lineages = []

    def on_signal(sig, frm):
        try:                                  # instrumentation: which signal ended the job, and when
            nm = signal.Signals(sig).name
            rec.log.event('signal', signal=sig, name=nm, elapsed_s=round(now() - T0, 1), left_s=round(left(), 1))
            rec.notes.append('ended by %s at %.1f s' % (nm, now() - T0))
        except Exception:
            pass
        rec.finish('timeout' if sig == signal.SIGALRM else 'killed', {'stages': stages_log})
        os._exit(3)
    signal.signal(signal.SIGALRM, on_signal)
    signal.signal(signal.SIGTERM, on_signal)
    # the job's hard end, on the realtime clock: signal.alarm runs on WSL's timer clock, 3-6 % fast (U5-1), and
    # ended 2700 s jobs at 2649 s real (2026-11-17 A/B)
    import threading
    def watchdog():
        while now() < T0 + a.seconds + 45:
            time.sleep(1.0)
        os.kill(os.getpid(), signal.SIGALRM)
    threading.Thread(target=watchdog, daemon=True).start()

    status = 'ok'; items_all = []; fates = {}; refused = []; plan_info = {}; sh_info = {}
    S = [x[2] for x in sched]; full_s = sum(S); s1_s = S[0] if S else 0; rest_s = full_s - s1_s
    registry = reg_load(a.registry)
    try:
        start = CM.load(a.inp)
        assert start.value_table() == CM.AES, 'start does not compute the %s' % CM.aesfn.label(function)
        d0 = CM.metrics(start)[3]; ctx.d0 = d0
        bp_cap = None if a.bp_cap == 'none' else (d0 + int(a.bp_cap[1:] or 0) if a.bp_cap.startswith('d') else int(a.bp_cap))
        log('start', CM.metrics(start), a.inp, 'kernel', ctx.bfx)
        spec = [x.strip() for x in a.conj.split(',') if x.strip()]
        # a conjugate is not conjugated again: refuse those items (explicitly), never replace them
        if any(x != 'id' for x in spec) and not a.allow_reconj and is_conjugated(a.inp):
            refused = [x for x in spec if x != 'id']; spec = [x for x in spec if x == 'id']
            rec.notes.append('start is a conjugate (file header / sidecar lineage): conjugates %s refused '
                             '(--allow-reconj overrides)' % refused); log(rec.notes[-1])
            rec.log.event('refused', items=refused, reason='start is a conjugate')
            if not spec:
                rec.finish('refused', {'stages': [], 'conj_refused': [{'label': x, 'reason': 'start is a conjugate'} for x in refused]})
                log('end refused')
                return 0
        screen_chosen = any(x == 'all' or x.startswith(('rank:', 'top:', 'sh:')) for x in spec)
        id_reg = reg_key(rec.start_sha, None, None, sched_spec(sched, range(len(sched))))
        id_first = 'id' not in spec and screen_chosen and (
            a.identity_first == 'yes' or (a.identity_first == 'auto' and not is_boolflux_output(a.inp)
                                          and not any(e['lam'] is None for e in registry.values()
                                                      if e.get('start_sha256') == rec.start_sha)))
        items = conj_list(','.join(spec), start, rec.start_sha, a, log)
        if id_first:
            items = [('id', None, None, None)] + items
            rec.notes.append('identity staged pull first (start is not a BoolFlux output; dropped after one stage '
                             'without a new point)')
        items_all[:] = items
        def nominal(its):
            return sum(full_s if x[1] != 'sh' else (min(x[2], len(a._sh_cands)) * s1_s + min(a.sh_keep, x[2]) * rest_s)
                       for x in its)
        need = nominal(items); avail = left() - RESERVE_S
        plan_info = {'need_s': round(need), 'avail_s': round(avail), 'schedule_s': full_s, 'items': [x[0] for x in items],
                     'identity_first': id_first}
        if need > avail:
            rec.notes.append('plan %.0f s (items x schedule) > %.0f s available: %s' % (
                need, avail, 'refused (--overrun refuse)' if a.overrun == 'refuse' else
                'stages of each item scaled to the time left / the remaining plan'))
            log(rec.notes[-1])
            if a.overrun == 'refuse':
                rec.log.event('plan', **plan_info, refused=True)
                rec.finish('refused', {'stages': [], 'plan': plan_info}); log('end refused')
                return 0
        rec.log.event('plan', **plan_info)
        rec.log.event('items', items=[list(x) for x in items], n=len(items))     # instrumentation: the conjugates chosen, in order

        def factor(this_s, after_s):
            """time share of the next segment: the time left over the remaining plan (this segment + the later
            ones, nominal seconds), at most 1; time an earlier lineage did not use goes to the later ones"""
            if this_s <= 0: return 1.0
            return max(0.0, min(1.0, (left() - RESERVE_S) / (this_s + after_s)))

        def new_lineage(name, lam, k, score, stall, rank=None):
            if lam is None:
                return Lineage(name, None, None, None, start, 'start', stall)
            t1 = now()
            cc = build_conj(start, lam, k, a.top_runs, bp_cap)
            nv = LAST_BUILD.get('naive')
            rec.log.event('conjugate', name=name, lam=lam, k=k, score=score, metrics=list(CM.metrics(cc)),
                          build_rng='random.Random(%d) (BP top), random.Random(1) (resynth)' % (lam * 8 + k),
                          build_s=round(now() - t1, 2), start_metrics=list(CM.metrics(start)), bp_cap=bp_cap,
                          n_tied=sum(1 for r in (getattr(a, '_rows', None) or []) if score is not None and r['sum'] == score),
                          n_within1=sum(1 for r in (getattr(a, '_rows', None) or []) if score is not None and r['sum'] <= score + 1),
                          file=keep_circuit(out, 'conj-%d-%d.bfx' % (lam, k), cc), **conj_mech(start, cc, lam, k))
            log('conjugate', name, lam, k, 'score', score, '->', CM.metrics(cc), '%.1fs' % (now() - t1))
            return Lineage(name, lam, k, score, cc, 'conj lam %d k %d (%s, score %s)' % (lam, k, name, score), stall,
                           naive=nv, screen_rank=rank)

        def run_stages(L, idx, f):
            """stages idx of lineage L, each at f x its seconds; returns False if the lineage was dropped"""
            ctx.L = L
            for si in idx:
                mode, cap, secs, rk, sseed = sched[si]
                if left() < 20:
                    rec.log.event('stop', what='stage loop', conj=L.name, reason='less than 20 s left', stage=si + 1)
                    L.dropped = 'time'; return False
                if L.stall and L.quiet >= L.stall:
                    L.dropped = 'lineage dropped: %d stages without a change in its (A, AD, G, GD) set' % L.quiet
                elif a.missed_pulls and L.missed >= a.missed_pulls:
                    L.dropped = 'lineage dropped: %d consecutive pulls ended above their cap (--missed-pulls %d)' % (
                        L.missed, a.missed_pulls)
                if L.dropped:
                    log(L.dropped)
                    rec.log.event('stop', what='stage loop', conj=L.name, reason=L.dropped, stage=si + 1,
                                  lineage_front=[list(p) for p in L.lin_front])
                    stages_log.append({'conj': L.name, 'dropped_after_stage': si, 'reason': L.dropped}); return False
                ctx.lin_changed = False
                gd_in = CM.metrics(L.cur)[3]
                D, planned = stage_cap(cap, gd_in, d0, si, a.caps == 'lineage', a.max_pull)
                starts = L.pareto or [L.cur]
                bests = []; seen = []
                for j in range(a.beam):
                    if left() < 20: break
                    rkk = rk if rk is not None else a.repair_keep
                    sd = (sseed + j) if sseed is not None else a.seed * 1000 + si * 10 + j
                    bud = min(secs * f, left() - 15)
                    base = starts[j % len(starts)]
                    L.lineage.append('stage %d %s:%d:%g seed %d rk %d' % (si + 1, mode, D, secs, sd, rkk))
                    t1 = now(); nw0 = len(rec.points); nk0 = ctx.ncall; ctx.stage_impr = []
                    b, par = run_stage(ctx, base, mode, D, bud, sd, rkk)
                    L.lineage.pop()
                    bests.append(b); seen += par
                    L.seconds += now() - t1
                    stages_log.append({'conj': L.name, 'lam': L.lam, 'k': L.k, 'stage': si + 1, 'mode': mode, 'cap': D,
                                       'cap_planned': planned, 'seed': sd, 'in': list(CM.metrics(base)),
                                       'best': list(CM.metrics(b)), 'seconds': round(now() - t1, 1), 'budget_factor': round(f, 3),
                                       'repair_keep': rkk, 'improvements': list(ctx.stage_impr)})
                    si_ = getattr(ctx, 'stage_info', None) or {}
                    sbf = keep_circuit(out, 'stage-%s-%d-%d-best.bfx' % (L.name.replace(':', '_'), si + 1, j), b)
                    rec.log.event('stage', **stages_log[-1], budget_s=round(bud, 1),
                                  written=len(rec.points) - nw0, kernel_calls=ctx.ncall - nk0, lineage_changed=ctx.lin_changed,
                                  substeps=si_.get('substeps'), stop=si_.get('stop'), file=sbf,
                                  pareto=[list(CM.metrics(x)) for x in par], **stage_mech(b, start, L.naive))
                    log('stage', si + 1, mode, D, 'seed', sd, CM.metrics(base), '->', CM.metrics(b), '%.0fs' % (now() - t1))
                feasD = lambda c: CM.metrics(c)[3] <= D
                if a.stage_choice == '4d':
                    k4 = lambda c: (0 if feasD(c) else 1,) + tuple(CM.metrics(c))
                else:                                     # as before 2026-11-17: feasible at D, then G, GD
                    k4 = lambda c: (0 if feasD(c) else 1, CM.metrics(c)[2], CM.metrics(c)[3])
                if bests:
                    bests.sort(key=k4); nxt = bests[0]
                    L.lineage.append('stage %d %s:%d best %s' % (si + 1, mode, D, '/'.join(map(str, CM.metrics(nxt)))))
                    L.cur = nxt
                    if a.stage_choice == '4d':            # beam seed j of the next stage starts from Pareto member j
                        fp = [c for c in pareto_circuits(seen + [nxt]) if feasD(c)]
                        L.pareto = ([nxt] + sorted((c for c in fp if c is not nxt), key=k4))[:max(1, a.beam)]
                pulled = D < gd_in
                L.missed = L.missed + 1 if (pulled and CM.metrics(L.cur)[3] > D) else 0
                L.quiet = 0 if ctx.lin_changed else L.quiet + 1
                L.stages_done = si + 1
                fates[L.name] = 'run: %d stages' % (si + 1)
                rec.write_result({'stages': stages_log})
            return True

        def reg_entry(L, idx):
            reg_add(a.registry, {'utc': CM.utc(), 'start_sha256': rec.start_sha, 'start': str(a.inp), 'lam': L.lam, 'k': L.k,
                                 'schedule': sched_spec(sched, idx), 'out': str(out), 'seed': a.seed})

        for ii, (name, lam, k, score) in enumerate(items):
            if left() < 30:
                for x in items[ii:]: fates[x[0]] = 'skipped: less than 30 s left'
                rec.log.event('stop', what='conjugate loop', reason='less than 30 s left', done=ii, of=len(items)); break
            after = nominal(items[ii + 1:])
            if lam != 'sh':
                key = reg_key(rec.start_sha, lam, k, sched_spec(sched, range(len(sched))))
                if key in registry:
                    fates[name] = 'skipped: registry (ran in %s)' % registry[key].get('out')
                    rec.log.event('registry-skip', item=name, lam=lam, k=k, ran_in=registry[key].get('out')); continue
                f = factor(full_s, after)
                if f < 1: rec.log.event('budget', item=name, factor=round(f, 3), after_s=round(after))
                L = new_lineage(name, lam, k, score, 1 if (id_first and ii == 0) else a.stall_stages)
                lineages.append(L); fates[name] = 'run: 0 stages'
                reg_entry(L, range(len(sched)))
                run_stages(L, range(len(sched)), f)
                continue
            # ---- successive halving: stage 1 on K conjugates, the rest of the schedule on the best sh_keep -------
            K = k; keep = max(1, min(a.sh_keep, K))
            k1 = sched_spec(sched, [0]); kr = sched_spec(sched, range(len(sched)))
            cands = [x for x in a._sh_cands if reg_key(rec.start_sha, x[1], x[2], k1) not in registry]
            nskip = len(a._sh_cands) - len(cands)
            cands = cands[:K]
            avail = left() - RESERVE_S - after
            while len(cands) > keep + 1 and len(cands) * s1_s + keep * rest_s > avail:
                cands.pop()                    # the worst screen-ranked one (the span keepers come first, dropped last)
            sh_info = dict(a._sh_info, K_asked=K, K=len(cands), keep=keep, registry_skipped=nskip, avail_s=round(avail),
                           candidates=[x[0] + '=%s:%s' % (x[1], x[2]) for x in cands])
            rec.log.event('halving', **sh_info)
            pool = []
            for ci, (cn, lam_, k_, sc) in enumerate(cands):
                if left() < 30:
                    fates[cn] = 'skipped: less than 30 s left'; continue
                after_c = (len(cands) - ci - 1) * s1_s + keep * rest_s + after
                f = factor(s1_s, after_c)
                rank_ = next((i + 1 for i, r in enumerate(getattr(a, '_rows', []) or []) if (r['lam'], r['k']) == (lam_, k_)), None)
                L = new_lineage(cn, lam_, k_, sc, a.stall_stages, rank=rank_)
                lineages.append(L); fates[cn] = 'run: 0 stages'
                reg_entry(L, [0])
                if run_stages(L, [0], f):
                    m = CM.metrics(L.cur); L.s1 = (m[0], m[1], m[2] + max(0, m[3] - d0), m[3]); pool.append(L)
            pool.sort(key=lambda L: L.s1)
            for r_, L in enumerate(pool): L.halving_rank = r_ + 1
            sh_info['ranking'] = [{'name': L.name, 'lam': L.lam, 'k': L.k, 'screen_rank': L.screen_rank,
                                   'after_stage1': list(CM.metrics(L.cur)), 'key': list(L.s1)} for L in pool]
            rec.log.event('halving-rank', ranking=sh_info['ranking'], keep=keep)
            for L in pool[keep:]:
                fates[L.name] = 'halving: stage 1 only (rank %d of %d)' % (L.halving_rank, len(pool))
            for qi, L in enumerate(pool[:keep]):
                if left() < 30: fates[L.name] += '; continuation skipped: less than 30 s left'; break
                f = factor(rest_s, (keep - qi - 1) * rest_s + after)
                reg_entry(L, range(len(sched)))
                run_stages(L, range(1, len(sched)), f)
        rec.log.event('item-fates', fates=fates, refused=refused)
    except Exception as e:
        import traceback
        status = 'error'; rec.notes.append(traceback.format_exc()[-1500:]); log('ERROR', repr(e))
    signal.alarm(0)
    run_ = [{'label': L.name, 'lam': L.lam, 'k': L.k, 'screen_score': L.score,
             'screen_rank': L.screen_rank if L.screen_rank is not None else (int(L.name[5:]) if L.name.startswith('rank:') else None),
             'stages_done': L.stages_done, 'stages_planned': len(sched), 'seconds': round(L.seconds, 1),
             'dropped': L.dropped, 'halving_rank': L.halving_rank, 'final': list(CM.metrics(L.cur)),
             'lineage_front': [list(p) for p in L.lin_front]} for L in lineages]
    planned = [x[0] for x in items_all] if items_all else None
    rec.finish(status, {'stages': stages_log, 'kernel_calls': ctx.ncall, 'conj_planned': planned, 'conj_run': run_,
                        'conj_not_reached': [x for x in (planned or []) if x not in fates and not x.startswith('sh:')],
                        'conj_refused': [{'label': x, 'reason': 'start is a conjugate'} for x in refused],
                        'fates': fates, 'plan': plan_info, 'halving': sh_info})
    log('end', status, 'written', len(rec.points), 'pareto', [p['tuple'] for p in rec.best_points()['pareto_G_GD']])
    return 0 if status == 'ok' else 1


if __name__ == '__main__':
    sys.exit(main())
