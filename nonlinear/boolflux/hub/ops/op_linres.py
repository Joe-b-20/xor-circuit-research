#!/usr/bin/env python3
"""Track-E hub operator linres: re-synthesis of one linear layer of a fixed AND structure, reading the
function bank.

    python3 hub/ops/op_linres.py --archive DIR --in ID --seed S --seconds T --out JOBDIR

Region R = all linear gates of one AND level k (convex: a path leaving R passes an AND and cannot come
back to level k).  Leaves = operands of R outside R; targets = R signals read outside R or outputs; every
target is an affine form over the leaves (Gaussian elimination on the complete truth tables).  Bank
functions (funcbank/bank.json, functions seen in any archived circuit) that lie in the leaves' span
become preferred intermediates: Paar's pair merging, where among the most frequent pairs the one whose
XOR is a bank function wins, and pairs that complete a bank function are merged even at frequency 1
(they are known to be useful elsewhere).  Remaining terms of each target are combined earliest-level
first.  Repeated with random tie-breaks until T; candidates the archive would place are returned.
"""
import json
import sys
import time
from pathlib import Path

OPS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(OPS_DIR.parents[1].parent))
from boolflux.hub import ops as HO                       # noqa: E402
from boolflux.hub.common import core, metrics, sbox, ONES   # noqa: E402

XOR, XNOR, NOT = 6, 9, 3


def layer_region(c, k):
    n = c.n; al = [0] * n
    for op, a, b in c.gates: al.append(max(al[a], al[b]) + (1 if op in core.NONLINEAR_OPS else 0))
    R = {n + j for j, (op, a, b) in enumerate(c.gates) if op not in core.NONLINEAR_OPS and al[n + j] == k}
    return R, al


def solve(c, R, tabs):
    n = c.n
    leaves = sorted({x for s in R for x in c.gates[s - n][1:] if x not in R})
    used = set(c.outputs)
    for t in range(n, n + len(c.gates)):
        if t in R: continue
        op, a, b = c.gates[t - n]; used.add(a); used.add(b)
    targets = [s for s in sorted(R) if s in used]
    piv = []
    basis = [ONES] + [tabs[x] for x in leaves]
    for i, t in enumerate(basis):
        f = 1 << i
        for p, rt, rf in piv:
            if (t >> p) & 1: t ^= rt; f ^= rf
        if t: piv.append((t.bit_length() - 1, t, f)); piv.sort(key=lambda r: -r[0])

    def form(t):
        f = 0
        for p, rt, rf in piv:
            if (t >> p) & 1: t ^= rt; f ^= rf
        return f if t == 0 else None
    return leaves, targets, form


def paar(rows, bankforms, rng):
    """rows: list of sets of term ids (1.. = leaves; const handled outside); returns list of (new_id, a, b)
    merges and the final rows"""
    rows = [set(r) for r in rows]; merges = []; nxt = max([max(r) for r in rows if r] + [0]) + 1
    termform = {}
    def tf(x): return termform.get(x, 1 << x)
    while True:
        cnt = {}
        for r in rows:
            bs = sorted(r)
            for i in range(len(bs)):
                for j in range(i + 1, len(bs)): cnt[(bs[i], bs[j])] = cnt.get((bs[i], bs[j]), 0) + 1
        if not cnt: break
        mx = max(cnt.values())
        best = [p for p, v in cnt.items() if v == mx]
        inbank = [p for p in best if (tf(p[0]) ^ tf(p[1])) in bankforms]
        if mx < 2:
            inbank = [p for p in cnt if (tf(p[0]) ^ tf(p[1])) in bankforms]
            if not inbank: break
            best = inbank
        p = rng.choice(inbank or best)
        t = nxt; nxt += 1; termform[t] = tf(p[0]) ^ tf(p[1]); merges.append((t, p[0], p[1]))
        for r in rows:
            if p[0] in r and p[1] in r: r.discard(p[0]); r.discard(p[1]); r.add(t)
    return merges, rows


def rebuild_layer(c, k, bank, rng):
    n = c.n; tabs = c.tables()
    R, al = layer_region(c, k)
    if len(R) < 3: return None
    leaves, targets, form = solve(c, R, tabs)
    tf = {}
    for s in targets:
        f = form(tabs[s])
        if f is None or f & ~1 == 0: return None
        tf[s] = f
    # bank functions in the leaves' span (forms without the constant)
    bankforms = set()
    for hx in bank:
        f = form(int(hx, 16))
        if f is not None and bin(f & ~1).count('1') >= 2: bankforms.add(f & ~1)
    rows = [{i for i in range(1, len(leaves) + 1) if (tf[s] >> i) & 1} for s in targets]
    merges, rows = paar(rows, bankforms, rng)
    # gates
    lv = [0] * n
    for op, a, b in c.gates: lv.append(1 + max(lv[a], lv[b]))
    gates = []; sig = {}; slv = {}
    keep = [s for s in range(n, n + len(c.gates)) if s not in R]
    # emit order: original non-R gates whose inputs are ready, region gates when their leaves are ready
    newid = {}
    pending = {i + 1: leaves[i] for i in range(len(leaves))}
    order = []      # (kind, payload)
    def term_sig(x):
        return sig[x]
    remap = {i: i for i in range(n)}
    # region signals are built lazily once all their leaves are mapped
    built_merge = set()
    def try_region():
        progress = True
        while progress:
            progress = False
            for (t, a, b) in merges:
                if t in sig: continue
                if a in sig and b in sig:
                    gates.append((XOR, sig[a], sig[b])); sig[t] = n + len(gates) - 1
                    slv[t] = 1 + max(slv[a], slv[b]); progress = True
            for s, r in zip(targets, rows):
                if s in remap: continue
                if all(x in sig for x in r):
                    xs = sorted(r, key=lambda x: slv[x])
                    while len(xs) > 1:
                        a, b = xs[0], xs[1]
                        gates.append((XOR, sig[a], sig[b])); g = n + len(gates) - 1
                        key = ('t', s, len(gates)); sig[key] = g; slv[key] = 1 + max(slv[a], slv[b])
                        xs = sorted(xs[2:] + [key], key=lambda x: slv[x])
                    created = len(r) > 1
                    g = sig[xs[0]]
                    if tf[s] & 1:
                        if created and gates[g - n][0] == XOR:
                            op, a2, b2 = gates[g - n]; gates[g - n] = (XNOR, a2, b2)
                        else:
                            gates.append((NOT, g, g)); g = n + len(gates) - 1
                    remap[s] = g; progress = True
    for i, x in enumerate(leaves):
        if x < n: sig[i + 1] = x; slv[i + 1] = 0
    try_region()
    for s in keep:
        op, a, b = c.gates[s - n]
        if a not in remap or b not in remap:
            return None
        gates.append((op, remap[a], remap[b])); remap[s] = n + len(gates) - 1
        for i, x in enumerate(leaves):
            if x == s: sig[i + 1] = remap[s]; slv[i + 1] = 0
        try_region()
    if any(o not in remap for o in c.outputs): return None
    nc = core.Circuit(n, c.m, gates, [remap[o] for o in c.outputs]).live()
    return nc if tuple(nc.value_table()) == sbox() else None


def op_linres(ar, args, rng, out):
    c = ar.circuit(args.inp); A, AD, G, GD = metrics(c)
    bf = Path(args.archive) / 'funcbank' / 'bank.json'
    bank = list(json.loads(bf.read_text()).keys()) if bf.exists() else []
    t0 = time.time(); cands = {}; tried = []
    while time.time() - t0 < args.seconds:
        k = rng.randrange(0, AD + 1)
        try:
            nc = rebuild_layer(c, k, bank, rng)
        except Exception as e:
            tried.append((k, 'error %s' % str(e)[:60])); continue
        if nc is None: tried.append((k, None)); continue
        m = metrics(nc); tried.append((k, m))
        if ar.would_place(m): cands[core.to_kernel(nc)] = nc
    cl = sorted(cands.values(), key=lambda x: (-ar.gain(metrics(x)), metrics(x)))
    return cl[:args.max_cands], {'tried': tried[:60], 'bank_size': len(bank)}


HO.OPS['linres'] = op_linres

if __name__ == '__main__':
    sys.exit(HO.main('linres'))
