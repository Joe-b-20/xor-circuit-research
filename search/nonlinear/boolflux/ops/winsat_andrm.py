#!/usr/bin/env python3
"""Window AND-removal check (2026-11-15; used by winsat.py mode andrm and the hub operator andrm): can a window with aW ANDs be rebuilt with aW - 1 ANDs?

Window W: convex, aW in {2, 3, 4} ANDs, K <= 10 inputs.  Window outputs t_h are taken on the
controllability care set (window-input patterns occurring over all 256 circuit inputs).
L = span(1, window inputs) on the care set; R = span of the outputs mod L, r = dim R.
- Any circuit with m ANDs over these inputs has its outputs in L + span(q_1..q_m) (q_j products of
  affine functions of inputs and earlier q's), so r <= m.  Hence r > aW - 1 => no (aW - 1)-AND
  rebuild of this window on this care set exists at all [C per window, status 'rank'].
- r = 0: the window is affine on its care set (all ANDs removable, status 'affine').
- else: FLAT products q = a*b, a, b affine over the window inputs (mod L only the input parts
  matter): every product is enumerated, those with residue in R kept; success if their residues span
  R with at most aW - 1 products (status 'removed'); otherwise 'no_flat' (exhaustive for flat products
  only; sequential products, AND of an AND, are not covered).
Hits are rebuilt (balanced XOR trees by arrival level), spliced, duplicate-merged and verified on all
256 inputs.  AND depth and gate depth may change; reported.

Library only (check_window, rebuild, windows); the driver is winsat.py --modes ...,andrm:P.
"""
import argparse, heapq, json, random, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent)); sys.path.insert(0, str(HERE))
from boolflux import core                         # noqa: E402
from boolflux.hub.common import metrics  # noqa: E402
import winsat_lib as R  # noqa: E402


class Span:
    """GF(2) span with canonical reduction (every pivot bit cleared) and combination tracking"""
    def __init__(self):
        self.piv = {}            # pivot bit -> (vec, combo)
        self.order = []          # pivot bits, descending

    def reduce(self, v, combo=0):
        for hb in self.order:
            if (v >> hb) & 1:
                pv, pc = self.piv[hb]; v ^= pv; combo ^= pc
        return v, combo

    def add(self, v, combo):
        r, c = self.reduce(v, combo)
        if not r: return False
        hb = r.bit_length() - 1
        for b in list(self.order):           # keep the basis fully reduced on the new pivot bit
            pv, pc = self.piv[b]
            if (pv >> hb) & 1: self.piv[b] = (pv ^ r, pc ^ c)
        self.piv[hb] = (r, c); self.order = sorted(self.piv, reverse=True)
        return True


def xor_tree(chain, leaves, k, lvl, negate):
    h = [(lvl[v], v) for v in leaves]; heapq.heapify(h)
    if len(h) == 1:
        v = h[0][1]
        if negate:
            chain.append((3, v, v)); nn = k + len(chain); lvl[nn] = lvl[v] + 1; return nn
        return v
    while len(h) > 1:
        la, a = heapq.heappop(h); lb, b = heapq.heappop(h)
        op = 9 if (negate and not h) else 6
        chain.append((op, a, b)); nn = k + len(chain); lvl[nn] = max(la, lb) + 1
        heapq.heappush(h, (lvl[nn], nn))
    return h[0][1]


def check_window(net, W, K):
    ins, outs = net.info(W)
    k = len(ins); aW = sum(1 for s in W if net.op(s) == R.AND)
    if k > K: return None
    P, vin, tg = R.care(net, ins, outs)
    mask = (1 << P) - 1
    L = Span()
    for gi, g in enumerate([mask] + vin): L.add(g, 1 << gi)
    RS = Span()
    for h, t in enumerate(tg): RS.add(L.reduce(t)[0], 0)
    r = len(RS.piv)
    det = {'k': k, 'o': len(outs), 'g': len(W), 'a': aW, 'P': P, 'dimL': len(L.piv), 'r': r}
    ctx = (ins, outs, vin, tg, L)
    if r == 0:
        det['status'] = 'affine'; return det, ctx, []
    if r > aW - 1:
        det['status'] = 'rank'; return det, ctx, None
    vals = [0] * (1 << k)
    for m in range(1, 1 << k):
        low = (m & -m).bit_length() - 1
        vals[m] = vals[m ^ (1 << low)] ^ vin[low]
    PS = Span(); prods = []
    for a in range(1, 1 << k):
        va = vals[a]
        for b in range(a + 1, 1 << k):
            q = va & vals[b]
            rq = L.reduce(q)[0]
            if not rq or RS.reduce(rq)[0]: continue        # residue 0 or outside R
            if PS.add(rq, 1 << len(prods)):
                prods.append((a, b, q))
                if len(prods) == r: break
        if len(prods) == r: break
    det['status'] = 'removed' if len(prods) == r else 'no_flat'
    return det, ctx, (prods if len(prods) == r else None)


def rebuild(net, ctx, prods):
    ins, outs, vin, tg, L = ctx
    k = len(ins); chain = []; lvl = {0: 0}
    for i, s in enumerate(ins): lvl[i + 1] = net.lv[s]
    # residue span of the chosen products, tracking which products
    PS = Span(); qn = []
    for j, (a, b, q) in enumerate(prods):
        PS.add(L.reduce(q)[0], 1 << j)
        la = [i + 1 for i in range(k) if (a >> i) & 1]; lb = [i + 1 for i in range(k) if (b >> i) & 1]
        na = xor_tree(chain, la, k, lvl, False); nb = xor_tree(chain, lb, k, lvl, False)
        chain.append((8, na, nb)); nn = k + len(chain); lvl[nn] = max(lvl[na], lvl[nb]) + 1; qn.append(nn)
    outmap = []
    for t in tg:
        rt = L.reduce(t)[0]
        z, use = PS.reduce(rt, 0)
        assert z == 0
        tt = t
        for j in range(len(prods)):
            if (use >> j) & 1: tt ^= prods[j][2]
        z2, c = L.reduce(tt, 0)
        assert z2 == 0
        leaves = [i for i in range(1, k + 1) if (c >> i) & 1] + [qn[j] for j in range(len(prods)) if (use >> j) & 1]
        if not leaves: return None                      # constant output
        outmap.append(xor_tree(chain, leaves, k, lvl, bool(c & 1)))
    # xor_tree numbering: local node of chain step s (0-based) is k + 1 + s; fix: we used k + len(chain)
    return chain, outmap


def windows(net, rng, K, maxg, maxo, amax):
    g = rng.choice(net.ands)
    near = {g}
    for _ in range(2):
        for s in list(near):
            near.update(x for x in net.ins[s] if x >= net.n); near.update(net.fo[s])
    mates = sorted(h for h in near if h != g and h >= net.n and net.op(h) == R.AND)
    if not mates: return None
    seeds = {g} | set(rng.sample(mates, min(len(mates), rng.choice([1, 1, 2]))))
    W = R.grow(net, seeds, rng, K, maxo, maxg, ming=2, fanin_only=rng.random() < 0.4, stop_at_and=True, greedy=0.5)
    if not W: return None
    aW = sum(1 for s in W if net.op(s) == R.AND)
    return W if 2 <= aW <= amax else None
