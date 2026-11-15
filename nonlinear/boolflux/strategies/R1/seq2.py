#!/usr/bin/env python3
"""Sequential 3 -> 2 AND check for windows where mc1's flat search failed (R1, 2026-11-15).

Window with aW = 3 ANDs and r = dim(outputs mod L) = 2.  A 2-AND rebuild has outputs in L + span(q1, q2),
q1 = a1*b1 (flat: a1, b1 affine over the window inputs X), q2 = u*v with u, v affine over X and q1.
Since r = 2 = m, R = span(res q1, res q2), so res(q1) lies in R: q1 ranges over the flat products with
residue in R \\ {0} (all of them, enumerated).  q2 cases (up to symmetry): (alpha + q1) * beta and
(alpha + q1) * (beta + q1), alpha, beta affine over X (constants included).  For a fixed beta the
product is affine in alpha, so the alphas giving q2 in L + R form an affine space found by one
elimination; a solution is kept if q2 is not in L + span(q1).  Together with mc1's flat search this is
exhaustive over all 2-AND circuits on the window inputs [C per window and care set].

    seq2.py CAMPAIGN MC1_JSONL OUT.jsonl [--ids-from FRONT_JSON] [--kmax 9]
"""
import argparse, json, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(next(p for p in HERE.parents if (p / 'boolflux' / 'core.py').exists()))); sys.path.insert(0, str(HERE))
from boolflux import core                         # noqa: E402
from boolflux.hub.common import metrics           # noqa: E402
import wres as R                                   # noqa: E402
from mc1 import Span, xor_tree                     # noqa: E402


def solve(gv, v0, LR, LQ):
    """alpha (bitmask over gv) with v0 + sum alpha_i gv_i in LR and not in LQ, or None"""
    S = Span()
    w0, _ = LR.reduce(v0)
    for i, g in enumerate(gv):
        w, _ = LR.reduce(g)
        S.add(w, 1 << i)
    r0, c0 = S.reduce(w0, 0)
    if r0: return None
    # kernel: generators whose reduced vector became dependent
    K = []
    T = Span()
    for i, g in enumerate(gv):
        w, _ = LR.reduce(g)
        rr, cc = T.reduce(w, 1 << i)
        if rr: T.add(w, 1 << i)
        else: K.append(cc)
    def val(al):
        v = v0
        for i, g in enumerate(gv):
            if (al >> i) & 1: v ^= g
        return v
    if LQ.reduce(val(c0))[0]: return c0
    for kv in K:
        if LQ.reduce(val(c0 ^ kv))[0]: return c0 ^ kv
    return None


def check(net, W, kmax):
    ins, outs = net.info(W); k = len(ins)
    if k > kmax: return None
    P, vin, tg = R.care(net, ins, outs)
    mask = (1 << P) - 1
    gens = [mask] + vin
    L = Span()
    for gi, g in enumerate(gens): L.add(g, 1 << gi)
    RS = Span()
    for t in tg: RS.add(L.reduce(t)[0], 0)
    if len(RS.piv) != 2: return {'status': 'r!=2', 'r': len(RS.piv)}, None
    LR = Span()
    for gi, g in enumerate(gens): LR.add(g, 0)
    for hb in RS.order: LR.add(RS.piv[hb][0], 0)
    vals = [0] * (1 << k)
    for m in range(1, 1 << k):
        low = (m & -m).bit_length() - 1
        vals[m] = vals[m ^ (1 << low)] ^ vin[low]
    Q1 = {}
    for a in range(1, 1 << k):
        for b in range(a + 1, 1 << k):
            q = vals[a] & vals[b]
            rq = L.reduce(q)[0]
            if rq and not RS.reduce(rq)[0] and q not in Q1: Q1[q] = (a, b)
    tried = 0
    for q1, (a1, b1) in Q1.items():
        LQ = Span()
        for g in gens: LQ.add(g, 0)
        LQ.add(q1, 0)
        for case in (1, 2):
            for beta in range(1, 1 << (k + 1)):        # bit 0 = constant, bits 1..k = inputs
                bv = (mask if beta & 1 else 0) ^ vals[beta >> 1]
                if case == 1:
                    if beta >> 1 == 0: continue          # constant beta
                    m2 = bv                              # q2 = (alpha + q1) * beta = alpha*bv + q1*bv
                else:
                    m2 = bv ^ q1                         # q2 = (alpha + q1) * (beta + q1)
                gv = [g & m2 for g in gens]              # alpha_i * m2
                v0 = q1 & m2
                tried += 1
                al = solve(gv, v0, LR, LQ)
                if al is not None:
                    return {'status': 'seq2', 'Q1': len(Q1), 'tried': tried}, (ins, outs, gens, tg, L, (a1, b1, q1), case, beta, al)
    return {'status': 'none', 'Q1': len(Q1), 'tried': tried}, None


def rebuild(net, sol):
    ins, outs, gens, tg, L, (a1, b1, q1), case, beta, al = sol
    k = len(ins); chain = []; lvl = {0: 0}
    for i, s in enumerate(ins): lvl[i + 1] = net.lv[s]
    la = [i + 1 for i in range(k) if (a1 >> i) & 1]; lb = [i + 1 for i in range(k) if (b1 >> i) & 1]
    na = xor_tree(chain, la, k, lvl, False); nb = xor_tree(chain, lb, k, lvl, False)
    chain.append((8, na, nb)); n1 = k + len(chain); lvl[n1] = max(lvl[na], lvl[nb]) + 1
    # u = alpha + q1
    lu = [i for i in range(1, k + 1) if (al >> i) & 1] + [n1]
    nu = xor_tree(chain, lu, k, lvl, bool(al & 1))
    lv_ = [i for i in range(1, k + 1) if (beta >> i) & 1] + ([n1] if case == 2 else [])
    nv = xor_tree(chain, lv_, k, lvl, bool(beta & 1))
    chain.append((8, nu, nv)); n2 = k + len(chain); lvl[n2] = max(lvl[nu], lvl[nv]) + 1
    # values of q2
    mask = gens[0]
    alv = 0
    for i, g in enumerate(gens):
        if (al >> i) & 1: alv ^= g
    bev = 0
    for i, g in enumerate(gens):
        if (beta >> i) & 1: bev ^= g
    q2 = (alv ^ q1) & (bev ^ (q1 if case == 2 else 0))
    PS = Span(); PS.add(L.reduce(q1)[0], 1); PS.add(L.reduce(q2)[0], 2)
    outmap = []
    for t in tg:
        z, use = PS.reduce(L.reduce(t)[0], 0)
        if z: return None
        tt = t ^ (q1 if use & 1 else 0) ^ (q2 if use & 2 else 0)
        z2, c = L.reduce(tt, 0)
        if z2: return None
        leaves = [i for i in range(1, k + 1) if (c >> i) & 1] + ([n1] if use & 1 else []) + ([n2] if use & 2 else [])
        if not leaves: return None
        outmap.append(xor_tree(chain, leaves, k, lvl, bool(c & 1)))
    return chain, outmap


def main():
    from boolflux.hub.archive import Archive
    ap = argparse.ArgumentParser()
    ap.add_argument('camp'); ap.add_argument('mc1'); ap.add_argument('out'); ap.add_argument('--kmax', type=int, default=9)
    ap.add_argument('--amax-circ', type=int, default=28)
    a = ap.parse_args()
    ar = Archive(a.camp)
    jobs = {}
    for l in open(a.mc1):
        d = json.loads(l)
        if d['status'] == 'no_flat' and d['a'] == 3 and d['r'] == 2 and d['m'][0] <= a.amax_circ and d['k'] <= a.kmax:
            jobs[(d['id'], tuple(d['W']))] = d
    print('windows', len(jobs), flush=True)
    outdir = Path(a.out).with_suffix(''); outdir.mkdir(parents=True, exist_ok=True)
    f = open(a.out, 'a'); nets = {}
    for (i, W), d in sorted(jobs.items(), key=lambda kv: kv[1]['k']):
        if i not in nets: nets[i] = (ar.circuit(i), R.Net(ar.circuit(i)))
        c, net = nets[i]
        t0 = time.time()
        rr = check(net, set(W), a.kmax)
        if rr is None: continue
        det, sol = rr
        det.update({'id': i, 'm': d['m'], 'W': list(W), 'k': d['k'], 'dt': round(time.time() - t0, 2)})
        if sol is not None:
            rb = rebuild(net, sol)
            if rb:
                ins, outs = sol[0], sol[1]
                nc = R.merge_dups(R.splice(c, net, set(W), ins, outs, *rb))
                det['ok'] = nc.output_tables() == c.output_tables(); det['m_new'] = metrics(nc)
                p = outdir / ('seq2-%s-%d.bfx' % (i, len(W))); p.write_text(core.to_kernel(nc)); det['file'] = str(p)
        f.write(json.dumps(det) + '\n'); f.flush()
        print(json.dumps(det), flush=True)


if __name__ == '__main__':
    main()
