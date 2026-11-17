#!/usr/bin/env python3
"""Operator `rebase`: exact re-basing of last-level product classes + depth-feasible hybrid rebuild
+ capped kernel (library: ops/rebase_lib/; any circuit with such classes).

    python3 search/nonlinear/boolflux/ops/rebase.py --in START --target REF --seed S --seconds T
        --out DIR [--cpus 1] [--cap D | --goal depth|gates] [--builds 160] [--top 3] [--stage-seconds 240]
        [--stages 2] [--moves [--descend]] [--move-budget 0.25] [--relax 0] [--slack3 0] [--no-paar] [--repair-keep 1]

Validated: a 177@13 archive circuit with --moves --stages 1 -> 35/3/181/12 after 469 s on one CPU;
a 168@13 circuit of NIST lineage with --cap 13 -> 35/3/167/13 after 489 s.

1. Classes (rebase_lib/gbasis.py): top products (feeding no AND) grouped by a common operand function Q;
   each class can be re-based (new R' = sums of old R's, A unchanged).  If no class exists: status
   "not-applicable" (result.json) and exit 0.
2. Cap D: --cap, else --goal depth: the lowest cap D in [GD-3, GD-1] whose re-basing bound (exact in
   the case of gbasis) is <= 1; --goal gates (default): D = min(target GD, start GD + 2) (re-basing
   moves at a gate-count cap).
3. Rounds: parent (with --moves the start is first scanned for GF(4) coordinate moves (AD3 GF(4) circuits
   of the forward or inverse S-box (rebase_lib/gf4fn.py: tables over the inversion input): hub/ops/gf4_lib
   gf4build keep2, priced by the bound, sharded over --cpus workers; --descend: a parent whose bound is
   above 1 keeps the moves with a strictly lower bound, so a chain of moves can descend to 1); variants with
   strictly more slack go first; then the start, then the run's own best results) -> feasible class
   combos -> hybrid builds at D (rebase_lib/hybrid.py, --paar shared layer) -> the --top lowest-G distinct
   builds -> --stages kernel stages (caps A <= ref A, AD <= ref AD, GD <= D; objective cost,gd);
   optional --relax S: one more kernel stage at D+1 (S s), whose result re-enters the pool as a parent.
4. Every verified circuit inside A/AD that is new in this run's (G, GD) front is recorded (rebuild_common).
5. --price gates (rebase_lib/gprice.py; default --price kraft = the combo order of step 3): a parent's candidates
   are priced by an estimate of the built circuit's gate count and the cheapest --builds are built with
   gprice.gbuild (hybrid generalised; a unit basis vector keeps the parent's product): Kraft-feasible combos of
   the top classes (up to --pool, gbasis DFS) ranked by price; with --deep also classes below the top AND level
   (gprice.find_classes; combos best-first by price with skeleton bound <= D); with --patch also patch builds
   (every parent gate kept, each replaced product redirected to the XOR of the new ones; single classes and
   pairs; only builds within the cap D are kept, as for the other builds).  No --moves in this mode.
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE / 'rebase_lib'))
sys.path.append(str(HERE.parent / 'hub' / 'ops' / 'gf4_lib'))     # GF(4) coordinate moves (--moves)
import rebuild_common as MC                           # noqa: E402
from rebuild_common import core, verify, metrics, clean, load, cid   # noqa: E402
import gbasis as GB                                   # noqa: E402
import hybrid as HY                                   # noqa: E402
import gprice as GP                                   # noqa: E402  (--price gates, --deep, --patch)
HY.new_skeleton = GB.new_skeleton                     # generalised skeleton (any classes, other output terms kept)



SCAN = {}       # instrumentation: summary of the last gf4_moves scan (counts, build / analyse seconds, stop reason)


def gf4_moves(c, cap, rng, budget_s, limit, shard='0/1'):
    """One-point GF(4) coordinate moves (keep2) of c, priced by the re-basing bound at cap; returns
    [(bound, G, circuit)] with bound <= limit, best first.  [] if c is not a GF(4)-tower AD3 circuit."""
    try:
        import gf4fn
        gf4fn.install()                 # GF(4) tables over the process's function's inversion input
        from nbscan import current_points
        from gf4build import build
        from pairs import Basis
        from boolflux.hub.common import _gmul
        pts0 = current_points(c)
    except Exception:
        return []
    si, sk = [int(x) for x in shard.split('/')]
    cand = [(i, p) for i in range(4) for p in range(1, 256) if (255 * i + p) % sk == si]
    rng.shuffle(cand)
    t0 = time.time(); seen = set(); out = []
    SCAN.clear(); SCAN.update(n=0, build_s=0.0, build_max=0.0, analyse_s=0.0, analyse_max=0.0, build_fail=0, basis_fail=0,
                              analyse_none=0, over_limit=0, candidates=len(cand), stop='exhausted')
    for i, p in cand:
        if time.time() - t0 > budget_s: SCAN['stop'] = 'budget'; break
        pts = list(pts0); pts[i] = p
        B = Basis([])
        if not all(B.add(_gmul(s, q)) for q in pts for s in (1, 188)): SCAN['basis_fail'] += 1; continue
        tb = time.time()
        try:
            nc = build(c, pts, keep2=True)
        except Exception:
            SCAN['build_fail'] += 1; continue
        finally:
            dtb = time.time() - tb; SCAN['build_s'] += dtb; SCAN['build_max'] = max(SCAN['build_max'], dtb)
        k = cid(nc)
        if k in seen: continue
        seen.add(k)
        ta = time.time(); SCAN['n'] += 1
        try:
            r = GB.analyse(nc, cap, ub=limit, value_only=True)   # bound exact when <= limit (gbasis docstring); only the bound is used
        except Exception:
            continue
        finally:
            dta = time.time() - ta; SCAN['analyse_s'] += dta; SCAN['analyse_max'] = max(SCAN['analyse_max'], dta)
        if r is None: SCAN['analyse_none'] += 1; continue
        dg = r.get('diag') or {}
        SCAN['max_merge_out'] = max(SCAN.get('max_merge_out', 0), max((x[2] for x in dg.get('merge', [])), default=0))
        SCAN['truncated'] = SCAN.get('truncated', 0) + bool(dg.get('truncated'))
        if r['best'] > limit + 1e-9: SCAN['over_limit'] += 1; continue
        out.append((r['best'], metrics(nc)[2], nc, pts))
    out.sort(key=lambda t: (t[0], t[1]))
    return out, len(seen)


def _js(combo):
    return json.loads(json.dumps(combo, default=str))


def gate_builds(par, res, D, a, rng, tl, L):
    """--price gates (docstring 5): priced candidates of one parent, built and verified.
    Returns (builds [(G, id, circuit, desc)], stats by id, all (G, GD, ok, in-cap), number of candidates, t0)."""
    tb = time.time(); P = GP.Parent(par); cand = []
    if res is not None and res['best'] <= 1 + 1e-9:
        cls_k = GP.gb_classes(res)
        for pr, cb in GP.priced_feasible(P, res, pool=a.pool, rng=rng)[:a.builds]:
            cand.append((pr, 'kraft', (cls_k, cb)))
    if a.deep:
        cls_d = GP.find_classes(P, deep=True)
        if cls_d:
            for pr, bd, cb, st in GP.ranked_combos(P, cls_d, D, rng, pool=a.builds):
                cand.append((pr, 'deep', (cls_d, cb, st)))
    cand.sort(key=lambda t: t[0])
    cand = cand[:a.builds]
    builds = []; hst = {}; allg = []; seen = set(); npr = len(cand)
    for pr, kind, pl in cand:
        if time.time() > tb + 0.25 * a.seconds: break
        try:
            if kind == 'kraft':
                st = GP.skeleton_of(P, pl[0], pl[1]); desc = {'kind': kind, 'price': pr, 'combo': [list(B) for B in pl[1]]}
            else:
                st = pl[2]; desc = {'kind': kind, 'price': pr, 'combo': [list(B) for B in pl[1]], 'classes': [pc['ands'] for pc in pl[0]]}
            if st is None: continue
            nc, stt = GP.gbuild(P, st, D, None, not a.no_paar)
        except Exception as e:
            L(event='build-error', err=repr(e)[:200]); continue
        k = cid(nc)
        if k in seen: continue
        seen.add(k)
        ok, inf = verify(nc); m = metrics(nc)
        allg.append((m[2], m[3], bool(ok), m[3] <= D and m[1] <= tl['AD']))
        if ok and m[3] <= D and m[1] <= tl['AD'] and m[0] <= tl['A']:
            builds.append((m[2], k, nc, desc)); hst[k] = stt
    if a.patch:
        try:
            pv, pcls = GP.patch_variants(par, deep=a.deep, max_single=a.patch_singles, max_pairs=a.patch_pairs, rng=rng)
        except Exception as e:
            pv = []; L(event='build-error', err='patch ' + repr(e)[:200])
        npr += len(pv)
        for nc, dsc in pv:
            k = cid(nc)
            if k in seen: continue
            seen.add(k)
            ok, inf = verify(nc); m = metrics(nc)
            allg.append((m[2], m[3], bool(ok), m[3] <= D and m[1] <= tl["AD"]))
            if ok and m[3] <= D and m[1] <= tl["AD"] and m[0] <= tl["A"]:
                builds.append((m[2], k, nc, {"kind": "patch", 'changes': [[ci, list(B)] for ci, B in dsc]}))
    return builds, hst, allg, npr, tb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='inp', required=True); ap.add_argument('--target', required=True)
    ap.add_argument('--seed', type=int, default=1); ap.add_argument('--seconds', type=float, required=True)
    ap.add_argument('--out', required=True); ap.add_argument('--cpus', type=int, default=1)
    ap.add_argument('--cap', type=int); ap.add_argument('--goal', choices=['depth', 'gates'])
    ap.add_argument('--builds', type=int, default=160); ap.add_argument('--top', type=int, default=3)
    ap.add_argument('--stage-seconds', type=float, default=240); ap.add_argument('--stages', type=int, default=2)
    ap.add_argument('--moves', action='store_true'); ap.add_argument('--move-top', type=int, default=4)
    ap.add_argument('--descend', action='store_true', help='with --moves: parents with bound > 1 keep strictly lower-bound moves')
    ap.add_argument('--move-budget', type=float, default=0.25, help='fraction of --seconds for one move scan')
    ap.add_argument('--relax', type=float, default=0); ap.add_argument('--slack3', type=int, default=0)
    ap.add_argument('--no-paar', action='store_true'); ap.add_argument('--repair-keep', type=int, default=1)
    ap.add_argument('--max-build-over', type=int, default=40, help='skip builds with G > best build + this')
    ap.add_argument('--price', choices=['kraft', 'gates'], default='kraft', help='gates: gate-cost pricing of candidates (docstring 5)')
    ap.add_argument('--deep', action='store_true', help='with --price gates: classes below the top AND level too')
    ap.add_argument('--patch', action='store_true', help='with --price gates: patch builds (no rebuild below the class)')
    ap.add_argument('--pool', type=int, default=3000, help='with --price gates: Kraft-feasible combos priced per parent')
    ap.add_argument('--patch-singles', type=int, default=40); ap.add_argument('--patch-pairs', type=int, default=120)
    ap.add_argument('--shard', default=None, help='i/K: this worker scans move candidates with index = i mod K (set by --cpus)')
    MC.C.function_arg(ap)
    a = ap.parse_args()
    MC.C.init_function(a)
    if a.shard is None: a.shard = '0/%d' % max(1, a.cpus)
    t0 = time.time(); deadline = t0 + a.seconds
    rng = random.Random(a.seed)
    HY.SLACK3 = bool(a.slack3)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    tl = MC.limits(a.target)
    params = {k: v for k, v in vars(a).items() if k not in ('inp', 'out', 'target', 'seed', 'seconds', 'cpus')}
    rec = MC.Recorder('rebase', a.target, out, a.inp, params, sys.argv, a.seed,
                      'ops/rebase.py: gbasis class re-basing + hybrid build + capped gate kernel')
    log = open(out / 'rebase.jsonl', 'a')

    def L(**kw):
        kw['t'] = round(time.time() - t0, 1); log.write(json.dumps(kw, default=str) + '\n'); log.flush()
        print(json.dumps(kw, default=str)[:300], flush=True)
    procs = MC.spawn_workers(sys.argv, a.cpus, a.seed, out) if a.cpus > 1 else []

    c0 = load(a.inp); m0 = metrics(c0)
    goal = a.goal or 'gates'
    # applicability and the cap
    r0 = GB.analyse(c0, m0[3], ub=1.0)
    gates_mode = a.price == 'gates'
    if gates_mode and a.moves: ap.error('--price gates does not take --moves')
    if r0 is None and gates_mode and (a.deep or a.patch):
        ncls = GP.find_classes(GP.Parent(c0), deep=a.deep)
        if ncls: r0 = {'class_sizes': [len(pc['ands']) for pc in ncls], 'n_top': None, 'diag': {'gprice_classes': True}}
    if r0 is None:
        rec.notes.append('no class of >= 2 top products with a common operand function')
        L(event='not-applicable', reason=rec.notes[-1]); rec.write('not-applicable'); return
    if a.cap:
        D = a.cap; goal = 'cap'
    elif goal == 'depth':
        D = None
        for d in range(m0[3] - 3, m0[3]):
            r = GB.analyse(c0, d, ub=1.0)
            L(event='bound', cap=d, best=r['best'], exact=r['exact'], current=r['current_max'], classes=r['class_sizes'])
            if r['best'] <= 1 + 1e-9: D = d; break
        if D is None:
            D = m0[3] - 1
            if not a.moves:
                rec.notes.append('re-basing bound > 1 at every cap GD-3..GD-1 (best %.3f at %d) and no --moves' % (r['best'], D))
                L(event='not-applicable', reason=rec.notes[-1]); rec.write('not-applicable'); return
    else:
        D = min(tl['GD'], m0[3] + 2)
    caps = {'A': tl['A'], 'AD': tl['AD'], 'GD': D}
    L(event='start', start=m0, cap=D, goal=goal, classes=r0['class_sizes'], top=r0['n_top'], caps=caps, analyse_diag=r0.get('diag'))
    pool = {}          # id -> (G, GD, circuit, how)
    queue = [(c0, 'start', str(Path(a.inp).resolve()))]
    scanned = set(); rnd = 0; used = {}; nbuilt = 0
    while time.time() < deadline - 60:
        if not queue:
            rnd += 1
            mem = sorted(pool.items(), key=lambda kv: (used.get(kv[0], 0), kv[1][1] > D, kv[1][0], kv[1][1]))
            for k, (g, gd, cc, how) in mem[:2]:
                queue.append((cc, how, None)); used[k] = used.get(k, 0) + 1
            if not queue: queue.append((c0, 'start', str(Path(a.inp).resolve())))
            if rnd > 50 and not pool: break
        par, how, ppath = queue.pop(0)
        if ppath is None:
            ppath = out / 'parents' / ('%s.bfx' % cid(par)); ppath.parent.mkdir(exist_ok=True); ppath.write_text(core.to_kernel(par))
        ta = time.time(); res = GB.analyse(par, D, ub=1.0); ta = time.time() - ta
        pk = cid(par)
        if gates_mode:
            builds, hst, allg, ncand, tb = gate_builds(par, res, D, a, rng, tl, L)
            if not builds and not ncand:
                L(event='analyse-none', parent=pk, how=how, secs=round(ta, 2)); continue
        elif res is None: L(event='analyse-none', parent=cid(par), how=how, secs=round(ta, 2)); continue
        def scan_moves():
            if a.moves and pk not in scanned and time.time() < deadline - 120:
                scanned.add(pk)
                lim = min(1.0, res['best']); pv = res['best']
                if a.descend and res['best'] > 1 + 1e-9:
                    # res (ub 1.0) only bounds the parent's value from above when it is above 1: take the exact one
                    pb = res['best'] if res.get('exact') else GB.analyse(par, D, ub=99.0, value_only=True)['best']
                    lim = pb - 1e-6; pv = pb
                mv = gf4_moves(par, D, rng, min(a.move_budget * a.seconds, deadline - 90 - time.time()), lim, a.shard)
                if mv:
                    mv, nseen = mv
                    L(event='moves', parent=pk, scanned=nseen, kept=len(mv), best=[(round(x[0], 3), x[1]) for x in mv[:8]],
                      scan={k: (round(v, 3) if isinstance(v, float) else v) for k, v in SCAN.items()})
                    strict = [x for x in mv if x[0] < pv - 1e-9]
                    for b, g, nc, pts in (strict or mv)[:a.move_top][::-1]:
                        item = (nc, 'move %s of %s (bound %.3f)' % (pts, pk, b), None)
                        if strict: queue.insert(0, item)      # strictly more slack: better parents, go first
                        else: queue.append(item)
                    return bool(strict)
            return False
        if gates_mode: pass
        elif a.moves and pk not in scanned and res['best'] <= 1 + 1e-9 and how == 'start':
            # scan first: if a coordinate move gives strictly more slack, build those variants before this parent
            if scan_moves():
                queue.append((par, how, ppath)); continue
        if gates_mode: pass
        elif res['best'] > 1 + 1e-9:
            L(event='skip', parent=pk, how=how, bound=res['best'])
            scan_moves()
            if not queue and not pool:
                rec.notes.append('no parent with re-basing bound <= 1 at cap %d' % D)
                break
            continue
        combos = [] if gates_mode else GB.feasible_combos(res, maxn=max(a.builds, 1) * 3, rng=rng)
        if not gates_mode: builds = []; tb = time.time(); allg = []; hst = {}
        for it, combo in enumerate(combos[:a.builds]):
            if time.time() > deadline - 60: break
            try:
                nc, st = HY.hybrid(par, res, list(combo), D, rng if it else None, not a.no_paar)
            except Exception as e:
                L(event='build-error', err=repr(e)[:200]); continue
            ok, inf = verify(nc); m = metrics(nc)
            allg.append((m[2], m[3], bool(ok), m[3] <= D and m[1] <= tl['AD']))
            if ok and m[3] <= D and m[1] <= tl['AD']:
                builds.append((m[2], cid(nc), nc, combo)); hst[cid(nc)] = st
        builds.sort(key=lambda t: t[0]); nbuilt += len(builds)
        seen = set(); pick = []
        for b in builds:
            if b[1] in seen or (pick and b[0] > pick[0][0] + a.max_build_over): continue
            seen.add(b[1]); pick.append(b)
            if len(pick) >= a.top: break
        L(event='builds', parent=pk, how=how, bound=(res['best'] if res is not None else None), n=len(builds), price=a.price, combos=len(combos),
          picked=[p[0] for p in pick], secs=round(time.time() - tb, 1), analyse_s=round(ta, 2), analyse_diag=(res or {}).get("diag"),
          all_builds=sorted(allg), picked_hybrid=[{'G': p[0], 'combo': _js(p[3]), 'stats': hst.get(p[1])} for p in pick])
        for g0, h, nc, combo in pick:
            if time.time() > deadline - 30: break
            meth = {'engine': 'ops/rebase.py (gbasis + hybrid + kernel)', 'cap': D, 'parent_how': how,
                    'combo': _js(combo), 'build_G': g0}
            bp = out / 'builds' / ('b-%s.bfx' % h); bp.parent.mkdir(exist_ok=True); bp.write_text(core.to_kernel(nc))
            rec.offer(nc, ppath, dict(meth, stage='build'))
            cur, cm = nc, metrics(nc)
            for st in range(a.stages):
                left = deadline - time.time() - 20
                if left < 20: break
                sd = rng.randrange(1, 10 ** 6)
                k, info = MC.kernel_stage(cur, caps, sd, min(a.stage_seconds, left), out / 'jobs' / ('%s-%d-%d' % (h, rnd, st)),
                                          repair_keep=a.repair_keep)
                if k is not None:
                    km = metrics(k)
                    if tuple(km) < tuple(cm): cur, cm = k, km     # value order (A, AD, G, GD); was (G, GD) only
                L(event='stage', build=h, G0=g0, stage=st, seed=sd, result=cm, err=info.get('error'),
                  t_last_improvement=info.get('t_last_improvement'), kernel_stats=info.get('kernel_stats'))
                rec.offer(cur, bp, dict(meth, stage='kernel', kernel_seed=sd, stage_index=st, caps=caps),
                          kernel_bin=info.get('kernel_bin_path'))
                for o in info.get('others') or []:       # other 4-D non-dominated kernel candidates (if the kernel returns several)
                    rec.offer(o, bp, dict(meth, stage='kernel-other', kernel_seed=sd, stage_index=st, caps=caps),
                              kernel_bin=info.get('kernel_bin_path'))
            pool[cid(cur)] = (cm[2], cm[3], cur, 'result of build %s' % h)
            if a.relax > 0 and time.time() < deadline - 60:
                sd = rng.randrange(1, 10 ** 6); rc = dict(caps, GD=D + 1)
                k, info = MC.kernel_stage(cur, rc, sd, min(a.relax, deadline - time.time() - 30), out / 'jobs' / ('%s-%d-relax' % (h, rnd)),
                                          repair_keep=a.repair_keep)
                if k is not None:
                    km = metrics(k)
                    L(event='relax', build=h, result=km)
                    rec.offer(k, bp, dict(meth, stage='relax', kernel_seed=sd, caps=rc), kernel_bin=info.get('kernel_bin_path'))
                    pool[cid(k)] = (km[2], km[3], k, 'relaxed result of build %s' % h)
        scan_moves()
    if procs: MC.merge_workers(rec, procs, deadline + 30)
    rec.write('ok' if nbuilt else 'not-applicable')
    L(event='end', front=sorted(rec.front))


if __name__ == '__main__':
    main()
