#!/usr/bin/env python3
"""Hub operator aslack (agent R2): affine-slack window redesign + short gate-kernel polish.

    op_aslack.py --archive DIR --in ID [--caps A,AD,GD] [--objective KEYS] --seed S --seconds T --out JOBDIR

Phase 1 (about 45% of T): random windows (2-5 ANDs at one AND level + their downstream linear logic,
optionally depth-limited); for each, new ANDs whose operands are affine in signals independent of the
window (AND level <= L-1) are searched so that every function the rest of the circuit needs from the
window lies in span(new ANDs, independent signals of level <= L, 1) (aslack.py); the window's linear
logic is re-synthesised, everything else is untouched; every rebuilt circuit is checked on all 256
inputs.  Some windows are chained (the next window is cut from the best raw result).
Phase 2: the best few raw results (lexicographic objective under the caps; A reductions first) are
polished with the gate kernel (hub ops._kernel, same settings as op_polish) for the remaining time.
Candidates: raw and polished circuits the archive would place, highest gain first.
"""
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(next(q for q in HERE.parents if (q / 'boolflux' / 'core.py').exists())))
from boolflux.hub import ops as HO                        # noqa: E402
from boolflux.hub.common import core, metrics, sbox       # noqa: E402
import aslack as AS                                       # noqa: E402

KEYIDX = {'a': 0, 'ad': 1, 'cost': 2, 'g': 2, 'gd': 3}


def lexkey(m, caps, keys):
    viol = 0
    for k, i in (('A', 0), ('AD', 1), ('GD', 3)):
        if caps.get(k) is not None and m[i] > caps[k]: viol += m[i] - caps[k]
    return (viol,) + tuple(m[KEYIDX[k]] for k in keys)


def op_aslack(ar, args, rng, out):
    c0 = ar.circuit(args.inp); m0 = metrics(c0)
    caps = args.caps or {'A': m0[0], 'AD': m0[1], 'GD': m0[3]}
    keys = [k.strip() for k in args.objective.split(',') if k.strip() in KEYIDX]
    t0 = time.time(); T1 = args.seconds * 0.4
    raw = {}                    # kernel text -> (circuit, metrics, info)
    st = {'windows': 0, 'spanned': 0, 'rebuilt': 0, 'func_ok': 0, 'func_bad': 0, 'a_red': 0, 'new_products': 0,
          'r_lt_k': 0, 'chained': 0}
    base = c0; I = AS.Info(c0); basem = m0
    while time.time() - t0 < T1:
        hunt = rng.random() < args.hunt          # A-hunt: bigger windows, retried until r < k
        W = None
        for _try in range(12 if hunt else 1):
            S = AS.choose_S(I, rng, kmax=8 if hunt else 5)
            if S is None: break
            mode = 'wide' if hunt else rng.choice(['wide', 'wide', 'local'])
            dd = rng.choice([None, 2, 3]) if hunt else rng.choice([None, 0, 1, 1, 2, 2, 3])
            try:
                W = AS.Window(I, S, mode, rng, ddepth=dd)
            except Exception:
                W = None; continue
            if not hunt or W.r < len(S): break
        if W is None: break
        st['windows'] += 1; st['hunt'] = st.get('hunt', 0) + hunt
        if hunt and W.r >= len(S): continue
        if W.r < len(S): st['r_lt_k'] += 1
        try:
            prods = W.products(rng, exhaustive_dim=10)
        except Exception as e:
            st["errors"] = st.get("errors", 0) + 1; continue
        if getattr(W, "exhaustive", False) and W.r < len(S): st["exh_r_lt_k"] = st.get("exh_r_lt_k", 0) + 1
        if hunt and W.r <= len(S) - 2:
            # m = r + e with e free products (e = 1 .. k - r - 1): products then may leave V + R
            ch0 = W.pick(prods, rng) if prods else None
            if ch0 is None:
                for _z in range(args.ztries):
                    e = rng.randint(1, len(S) - W.r - 1)
                    W2 = W.extended([W.random_product(rng) for _ in range(e)])
                    if W2.r >= len(S): continue
                    p2 = W2.products(rng, exhaustive_dim=10)
                    st['ext_tries'] = st.get('ext_tries', 0) + 1
                    if p2 and W2.pick(p2, rng) is not None:
                        st['ext_found'] = st.get('ext_found', 0) + 1
                        W = W2; prods = p2; break
        if not prods: continue
        for rep in range(3):
            ch = W.pick(prods, rng, noise=0.5 + rep)
            if ch is None:
                if W.r < len(S): st.setdefault('r_lt_k_unspanned', []).append([len(S), W.r, W.L, getattr(W, 'exhaustive', False)])
                break
            if W.r < len(S) and rep == 0: st.setdefault('r_lt_k_spanned', []).append([len(S), W.r, W.L])
            st['spanned'] += 1
            try:
                rows = W.target_rows(ch, rng)
            except Exception:
                st["errors"] = st.get("errors", 0) + 1; rows = None
            if rows is None: continue
            try:
                nc = AS.rebuild(W, ch, rows, rng)
            except Exception:
                nc = None
            if nc is None: continue
            st['rebuilt'] += 1
            if tuple(nc.value_table()) != sbox(): st['func_bad'] += 1; continue
            st['func_ok'] += 1
            m = metrics(nc)
            newp = sum(1 for p in ch if not any(p[4] == I.tabs[s] for s in S))
            if newp: st['new_products'] += 1
            if m[0] < basem[0]: st['a_red'] += 1
            k = core.to_kernel(nc)
            if k not in raw:
                raw[k] = (nc, m, {'k': len(S), 'L': W.L, 'm_new': len(ch), 'r': W.r, 'mode': mode, 'dd': dd,
                                  'new_products': newp, 'chain': base is not c0})
        # chaining: sometimes continue from a raw result that is not worse in the objective by much
        if raw and rng.random() < 0.3:
            best = min(raw.values(), key=lambda v: lexkey(v[1], caps, keys))
            if lexkey(best[1], caps, keys)[:2] <= lexkey(basem, caps, keys)[:2] and best[0] is not base:
                base = best[0]; basem = best[1]; I = AS.Info(base); st['chained'] += 1
        elif rng.random() < 0.1:
            base = c0; basem = m0; I = AS.Info(c0)
    # phase 2: polish the best raw results
    ranked = sorted(raw.values(), key=lambda v: lexkey(v[1], caps, keys))
    # keep structural variety: at most 2 from the same (A, G) and prefer new products
    pol = []; seenAG = {}
    for v in ranked:
        kk = (v[1][0], v[1][2])
        if seenAG.get(kk, 0) >= 2: continue
        seenAG[kk] = seenAG.get(kk, 0) + 1; pol.append(v)
        if len(pol) >= args.npolish: break
    cands = {}
    for v in ranked[:200]:
        if ar.would_place(v[1]): cands[core.to_kernel(v[0])] = (v[0], v[1], dict(v[2], polished=False))
    left = args.seconds - (time.time() - t0)
    pinfo = []
    for j, v in enumerate(pol):
        left = args.seconds - (time.time() - t0)
        secs = max(2.0, left / (len(pol) - j)) - 0.5
        if left < 2.5: break
        pd = out / ('p%d' % j); pd.mkdir(exist_ok=True)
        try:
            pc, info = HO._kernel(v[0], caps, args.objective, rng.randrange(1, 1 << 30), round(secs, 1), pd, args.archive)
        except Exception as e:
            pinfo.append({'error': repr(e)[:100]}); continue
        if not pc: pinfo.append({"from": v[1], "to": None, "secs": round(secs, 1)})
        for c in pc:
            m = metrics(c)
            pinfo.append({'from': v[1], 'to': m, 'secs': round(secs, 1)})
            if ar.would_place(m): cands[core.to_kernel(c)] = (c, m, dict(v[2], polished=True, raw=v[1]))
    cl = sorted(cands.values(), key=lambda x: (-ar.gain(x[1]), lexkey(x[1], caps, keys)))[:args.max_cands]
    st['raw_distinct'] = len(raw)
    st['best_raw'] = ranked[0][1] if ranked else None
    return [x[0] for x in cl], {'caps': caps, 'stats': st, 'polish': pinfo, 'cands': [[x[1], x[2]] for x in cl]}


HO.OPS['aslack'] = op_aslack

if __name__ == '__main__':
    # extra option: --npolish (default 3)
    argv = sys.argv[1:]; npol = 3; hunt = 0.15
    if '--npolish' in argv:
        i = argv.index('--npolish'); npol = int(argv[i + 1]); del argv[i:i + 2]
    if '--hunt' in argv:
        i = argv.index('--hunt'); hunt = float(argv[i + 1]); del argv[i:i + 2]
    _orig = HO.argparse.ArgumentParser.parse_args

    def _pa(self, a=None, ns=None):
        r = _orig(self, a, ns); r.npolish = npol; r.hunt = hunt; r.ztries = 4; return r
    HO.argparse.ArgumentParser.parse_args = _pa
    sys.exit(HO.main('aslack', argv))
