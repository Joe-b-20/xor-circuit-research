#!/usr/bin/env python3
"""Window-resynthesis optimiser (track D).

    python3 run.py --start FILE --out DIR [--seconds 3600] [--seed 1]
                   [--cap-gd D] [--cap-ad D] [--cap-a A]     (default: the start's own values)
                   [--mode g|depth] [--target-gd T --gmax G] (depth mode: reach GD <= T)
                   [--kmin 4 --kmax 9 --cmax 12 --mmax 7 --ndiv 3 --budget 30000]
                   [--neutral 0.0]

Mode g: repeatedly pick a random convex window, try to resynthesise it with r = k-1, k-2, ...
gates (AND count within the A cap), or with k gates and fewer ANDs; never exceed the caps.
Mode depth: windows on critical paths (level + tail > T) are resynthesised so that all window
outputs meet the required levels for cap T, with up to (gmax - G) extra gates; the number of
critical signals strictly decreases, and on reaching GD <= T the run continues in mode g at T.
Every accepted circuit is re-simulated on all 256 inputs.  Output: DIR/log.jsonl (one line per
accepted move), DIR/cur.circ.txt (checkpoint), DIR/best-*.circ.txt + .json sidecars.
"""
import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

import wresyn as R
from boolflux import core

MODEL = core.Model.load('nist')


def crit_mask(st, T):
    return [st.lg[s] + st.tg[s] > T for s in range(st.S)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--seconds', type=float, default=3600)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--cap-gd', type=int)
    ap.add_argument('--cap-ad', type=int)
    ap.add_argument('--cap-a', type=int)
    ap.add_argument('--mode', default='g')
    ap.add_argument('--target-gd', type=int)
    ap.add_argument('--gmax', type=int)
    ap.add_argument('--kmin', type=int, default=4)
    ap.add_argument('--kmax', type=int, default=9)
    ap.add_argument('--cmax', type=int, default=12)
    ap.add_argument('--mmax', type=int, default=7)
    ap.add_argument('--ndiv', type=int, default=3)
    ap.add_argument('--budget', type=int, default=30000)
    ap.add_argument('--neutral', type=float, default=0.0)
    ap.add_argument('--depth-slack', type=int, default=2)
    ap.add_argument('--win', default='grow', help='grow | cut | mix (window selection)')
    ap.add_argument('--cutk', type=int, default=6, help='max cut size for cut windows')
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    cur = core.read_ncff(args.start).live()
    assert R.correct(cur)
    st = R.State(cur)
    capGD = args.cap_gd if args.cap_gd is not None else st.GD
    capAD = args.cap_ad if args.cap_ad is not None else st.AD
    capA = args.cap_a if args.cap_a is not None else st.A
    mode = args.mode
    T = args.target_gd
    gmax = args.gmax
    if mode == 'depth':
        assert T is not None and gmax is not None
    t0 = time.time()
    logf = open(out / 'log.jsonl', 'a')
    stats = {'win': 0, 'skip': 0, 'sat': 0, 'unsat': 0, 'unk': 0, 'acc': 0, 'neutral': 0}
    start_m = cur.metrics()

    def log(d):
        d['t'] = round(time.time() - t0, 2)
        logf.write(json.dumps(d) + '\n')
        logf.flush()

    log({'event': 'start', 'args': vars(args), 'metrics': {k: start_m[k] for k in ('G', 'A', 'GD', 'AD')},
         'caps': [capA, capAD, capGD], 'pid': os.getpid()})
    best_key = None
    moves = []

    def save_best(c, tag):
        m = c.metrics()
        name = 'best-%s-g%d-a%d-gd%d-ad%d' % (tag, m['G'], m['A'], m['GD'], m['AD'])
        p = out / (name + '.circ.txt')
        p.write_text(core.write_ncff(c, MODEL, comments=['track D window resynthesis from %s' % Path(args.start).name]),
                     encoding='utf-8')
        side = {'start': str(Path(args.start).resolve()), 'command': ' '.join(sys.argv), 'seed': args.seed,
                'metrics': {k: m[k] for k in ('G', 'A', 'GD', 'AD')}, 'time_to_result_s': round(time.time() - t0, 2),
                'moves': list(moves), 'stats': dict(stats)}
        (out / (name + '.json')).write_text(json.dumps(side, indent=1) + '\n', encoding='utf-8')
        return p

    tried = set()
    cuts = None
    cuts_ver = -1
    last_ck = time.time()
    while time.time() - t0 < args.seconds:
        if time.time() - last_ck > 60:
            (out / 'cur.circ.txt').write_text(core.write_ncff(cur, MODEL), encoding='utf-8')
            log({'event': 'ck', 'stats': dict(stats), 'cur': (st.G, st.A, st.GD, st.AD), 'mode': mode})
            last_ck = time.time()
        if mode == 'depth':
            crit = crit_mask(st, T)
            ncrit = sum(crit)
            if ncrit == 0:
                save_best(cur, 'depth')
                log({'event': 'depth_reached', 'G': st.G, 'A': st.A, 'GD': st.GD, 'AD': st.AD})
                mode = 'g'
                capGD = T
                tried.clear()
                continue
            seeds = [s for s in range(st.n, st.S) if crit[s]]
        else:
            crit = None
            seeds = list(range(st.n, st.S))
        k = rng.randint(args.kmin, args.kmax)
        use_cut = args.win == 'cut' or (args.win == 'mix' and rng.random() < 0.5)
        if use_cut:
            if cuts is None or cuts_ver != stats['acc']:
                cuts = R.enum_cuts(st, args.cutk, 24, rng)
                cuts_ver = stats['acc']
            root = rng.choice(seeds)
            cs = [u for u in cuts[root] if len(u) >= 3]
            W = R.cut_window(st, root, rng.choice(cs), k, rng) if cs else None
        else:
            W = R.grow_window(st, rng.choice(seeds), k, rng, args.cmax, crit=crit)
        stats['win'] += 1
        if W is None:
            stats['skip'] += 1
            continue
        nd = rng.randint(0, args.ndiv)
        key = (frozenset(W), nd)
        if key in tried:
            stats['skip'] += 1
            continue
        tried.add(key)
        w = R.analyse(st, W, ndiv=nd, rng=rng, mmax=args.mmax, cmax=args.cmax,
                      capGD=(T if mode == 'depth' else capGD), capAD=capAD)
        if w is None:
            stats['skip'] += 1
            continue
        a_room = capA - (st.A - w.a)
        found = None
        ts = time.time()
        if mode == 'g':
            if min(w.req_g) < 0:
                stats['skip'] += 1
                continue
            r = w.k - 1
            while r >= 0:
                res, sol = R.solve(w, r, min(a_room, r), budget=args.budget)
                if res:
                    found = (r, sol)
                    stats['sat'] += 1
                    r -= 1
                else:
                    stats['unsat' if res is False else 'unk'] += 1
                    break
            if found is None and w.a > 0:
                res, sol = R.solve(w, w.k, w.a - 1, budget=args.budget)
                if res:
                    found = (w.k, sol)
                    stats['sat'] += 1
                else:
                    stats['unsat' if res is False else 'unk'] += 1
            if found is None and args.neutral > 0 and w.internal and rng.random() < args.neutral:
                gq = rng.choice(w.internal)
                fv = [(st.tab[gq] >> x_) & 1 for x_ in w.rep]
                res, sol = R.solve(w, w.k, w.a, budget=args.budget, forbid=[fv])
                if res:
                    found = (w.k, sol)
                    stats['neutral'] += 1
        else:
            room = gmax - st.G
            for r in range(max(0, w.k - 2), w.k + min(args.depth_slack, room) + 1):
                res, sol = R.solve(w, r, min(a_room, r), budget=args.budget)
                if res:
                    found = (r, sol)
                    stats['sat'] += 1
                    break
                stats['unsat' if res is False else 'unk'] += 1
                if res is None:
                    break
        tsat = time.time() - ts
        if found is None:
            continue
        r, (prog, outsel) = found
        assert R.sim_check(w, prog, outsel, st)
        nc = R.apply(st, w, prog, outsel).live()
        if not R.correct(nc):
            log({'event': 'BUG_incorrect', 'win': w.gates})
            continue
        m = nc.metrics()
        if m['GD'] > (capGD if mode == 'g' else st.GD) or m['AD'] > capAD or m['A'] > capA:
            log({'event': 'BUG_cap', 'metrics': m})
            continue
        if mode == 'g':
            better = (m['G'], m['A']) < (st.G, st.A)
            neutral = (m['G'], m['A']) == (st.G, st.A)
            if not better and not (neutral and nc.gates != cur.gates):
                continue
        else:
            nst = R.State(nc)
            if sum(crit_mask(nst, T)) >= ncrit or m['G'] > gmax:
                continue
        old = (st.G, st.A, st.GD, st.AD)
        cur = nc
        st = R.State(cur)
        tried.clear()
        stats['acc'] += 1
        mv = {'event': 'accept', 'mode': mode, 'k': w.k, 'r': r, 'a_old': w.a,
              'a_new': sum(1 for g in prog if g[0] == R.AND), 'ncut': w.ncut, 'ndiv': len(w.ins) - w.ncut,
              'm': len(w.outs), 'P': len(w.pats), 'nfree': w.nfree, 'tsat': round(tsat, 2),
              'before': old, 'after': (st.G, st.A, st.GD, st.AD),
              'old_ops': [core.OPNAME[op_] for op_ in w.old_ops],
              'new_prog': prog, 'outsel': outsel}
        if mode == 'depth':
            mv['ncrit_before'] = ncrit
            mv['ncrit_after'] = sum(crit_mask(st, T))
        log(mv)
        moves.append(dict(mv))
        if mode == 'g':
            bk = (st.G, st.A)
            if best_key is None or bk < best_key:
                best_key = bk
                if bk < (start_m['G'], start_m['A']):
                    save_best(cur, 'g')
    (out / 'cur.circ.txt').write_text(core.write_ncff(cur, MODEL), encoding='utf-8')
    log({'event': 'end', 'stats': stats, 'cur': (st.G, st.A, st.GD, st.AD)})
    print(json.dumps({'stats': stats, 'cur': (st.G, st.A, st.GD, st.AD), 'start': (start_m['G'], start_m['A'], start_m['GD'], start_m['AD'])}))


if __name__ == '__main__':
    main()
