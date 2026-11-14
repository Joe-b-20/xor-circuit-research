#!/usr/bin/env python3
"""Timing-driven regional rebuild of linear logic (track F).

A region R is a convex set of linear gates (XOR/XNOR/NOT) of a circuit that meets gate-depth
cap D.  Leaves = operands of R's gates outside R (arrival = their level, unchanged because R is
convex); targets = R's gates used outside R or as outputs, each with its exact required level
for cap D (from the unchanged consumers).  Every target is an affine form over the leaves.  The
targets are re-synthesised by a randomised Paar-style pair merging that keeps, for every
target, Kraft's condition sum 2^(level - required) <= 1 over its current cover (so the final
depth-optimal XOR tree of every target meets its deadline), then each cover is finished by a
Huffman tree (earliest two first).  The result meets cap D by construction.

Regions: 'bottom' (linear gates after the last AND level), 'top' (no AND in the fan-in),
'mid' (one AND level k chosen at random among the middle ones), 'random' (fan-in cone of a
random linear gate inside its AND-level layer, 6-30 gates, closed to be convex).

    python3 trb.py FILE --cap D --region bottom --seed 1 [--out OUT.circ.txt]
"""
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core, targets   # noqa: E402

AND, XOR, XNOR, NOT = 8, 6, 9, 3
INF = 10 ** 9


def struct(c, D):
    n = c.n; S = n + len(c.gates)
    lv = [0] * S; al = [0] * S; fo = [[] for _ in range(S)]
    for j, (op, a, b) in enumerate(c.gates):
        s = n + j
        lv[s] = 1 + max(lv[a], lv[b]); al[s] = (1 if op == AND else 0) + max(al[a], al[b])
        fo[a].append(s)
        if b != a: fo[b].append(s)
    req = [INF] * S
    for o in c.outputs: req[o] = min(req[o], D)
    for s in range(S - 1, n - 1, -1):
        if req[s] == INF: continue
        op, a, b = c.gates[s - n]
        req[a] = min(req[a], req[s] - 1); req[b] = min(req[b], req[s] - 1)
    return lv, al, req, fo


def pick_region(c, kind, rng, lv, al, fo):
    n = c.n
    lin = [s for s in range(n, n + len(c.gates)) if c.gates[s - n][0] != AND]
    if not lin: return set()
    amax = max(al[s] for s in lin)
    if kind == 'bottom': R = {s for s in lin if al[s] == amax}
    elif kind == 'top': R = {s for s in lin if al[s] == 0}
    elif kind == 'mid':
        ks = sorted({al[s] for s in lin if 0 < al[s] < amax})
        if not ks: return set()
        k = rng.choice(ks); R = {s for s in lin if al[s] == k}
    else:
        K = rng.randint(6, 30)
        root = rng.choice(lin); layer = al[root]
        R = set(); fr = [root]
        while fr and len(R) < K:
            s = fr.pop(rng.randrange(len(fr)))
            if s in R: continue
            R.add(s)
            op, a, b = c.gates[s - n]
            for x in (a, b):
                if x >= n and c.gates[x - n][0] != AND and al[x] == layer and x not in R: fr.append(x)
            # also grow towards fan-out inside the layer sometimes
            if rng.random() < 0.3:
                for y in fo[s]:
                    if c.gates[y - n][0] != AND and al[y] == layer and y not in R: fr.append(y)
        # convexity: add every linear gate of the layer on a path R -> outside -> R
        changed = True
        while changed:
            changed = False
            # nodes reachable from R (outside R)
            reach = set(); st = [y for s in R for y in fo[s] if y not in R]
            while st:
                y = st.pop()
                if y in reach: continue
                reach.add(y); st += [z for z in fo[y] if z not in R]
            # R gates with an operand in reach -> that operand's path must be absorbed
            for s in list(R):
                op, a, b = c.gates[s - n]
                for x in (a, b):
                    if x in reach:
                        if x >= n and c.gates[x - n][0] != AND and al[x] == layer:
                            R.add(x); changed = True
                        else:
                            R.discard(s); changed = True
                        break
    return R


def rebuild(c, D, kind, rng, region=None):
    """Return (new circuit, info).  Raises nothing: on failure returns the input."""
    n = c.n
    lv, al, req, fo = struct(c, D)
    R = region if region is not None else pick_region(c, kind, rng, lv, al, fo)
    if len(R) < 2: return c, {'region_gates': len(R), 'skipped': 1}
    outset = set(c.outputs)
    leaves = sorted({x for s in R for x in c.gates[s - n][1:] if x not in R})
    li = {x: i for i, x in enumerate(leaves)}
    form = {}
    for s in sorted(R):
        op, a, b = c.gates[s - n]
        fa = form[a] if a in R else (1 << (1 + li[a]))
        fb = form[b] if b in R else (1 << (1 + li[b]))
        if op == XOR: f = fa ^ fb
        elif op == XNOR: f = fa ^ fb ^ 1
        elif op == NOT: f = fa ^ 1
        else: raise ValueError('non-linear gate in region')
        form[s] = f
    tg = [s for s in sorted(R) if s in outset or any(y not in R for y in fo[s])]
    # signals of the rebuild: id -> (level, form); leaves first
    sig_lv = [lv[x] for x in leaves]
    sig_form = [1 << (1 + i) for i in range(len(leaves))]
    sig_gate = [None] * len(leaves)           # (a_id, b_id) for new XORs
    byform = {f: i for i, f in enumerate(sig_form)}
    covers = {}; const = {}; dl = {}
    for t in tg:
        f = form[t]; const[t] = f & 1; dl[t] = req[t]
        covers[t] = [li_ for li_ in range(len(leaves)) if (f >> (1 + li_)) & 1]
        if not covers[t]: return c, {'skipped': 1, 'why': 'constant target'}
    def kraft_ok(t, cov):
        r = dl[t]
        if len(cov) == 1:
            return sig_lv[cov[0]] + (1 if const[t] else 0) <= r
        return sum(2.0 ** (sig_lv[x] - r) for x in cov) <= 1.0 + 1e-12
    for t in tg:
        if not kraft_ok(t, covers[t]):
            return c, {'skipped': 1, 'why': 'infeasible start'}
    # randomised Paar with Kraft checks
    while True:
        cnt = {}
        for t in tg:
            cv = covers[t]
            if len(cv) < 2: continue
            for i in range(len(cv)):
                for j in range(i + 1, len(cv)):
                    p = (cv[i], cv[j]) if cv[i] < cv[j] else (cv[j], cv[i])
                    cnt[p] = cnt.get(p, 0) + 1
        if not cnt: break
        # score: count, prefer equal levels; random noise for diversity
        cands = sorted(cnt.items(), key=lambda kv: (-(kv[1] - 0.3 * abs(sig_lv[kv[0][0]] - sig_lv[kv[0][1]]) + 0.5 * rng.random())))
        done = False
        for (u, v), k in cands[:20]:
            if k < 2: break
            w_lv = max(sig_lv[u], sig_lv[v]) + 1
            users = []
            for t in tg:
                cv = covers[t]
                if u in cv and v in cv:
                    new = [x for x in cv if x != u and x != v] + [-1]
                    # evaluate with w's level
                    r = dl[t]
                    if len(new) == 1: ok = w_lv + (1 if const[t] else 0) <= r
                    else: ok = sum(2.0 ** ((sig_lv[x] if x >= 0 else w_lv) - r) for x in new) <= 1.0 + 1e-12
                    if ok: users.append(t)
            if len(users) >= 2:
                fw = sig_form[u] ^ sig_form[v]
                w = byform.get(fw)
                if w is None or sig_lv[w] > w_lv:
                    w = len(sig_lv); sig_lv.append(w_lv); sig_form.append(fw); sig_gate.append((u, v)); byform[fw] = w
                for t in users:
                    covers[t] = [x for x in covers[t] if x != u and x != v] + [w]
                done = True; break
        if not done: break
    # finish every target with a Huffman tree over its cover
    import heapq
    tsig = {}
    for t in tg:
        cv = covers[t]
        if len(cv) == 1:
            tsig[t] = (cv[0], const[t]); continue
        h = [(sig_lv[x], rng.random(), x) for x in cv]; heapq.heapify(h)
        while len(h) > 1:
            l1, _, x = heapq.heappop(h); l2, _, y = heapq.heappop(h)
            fw = sig_form[x] ^ sig_form[y]; wl = max(l1, l2) + 1
            w = byform.get(fw)
            if w is None or sig_lv[w] > wl:
                w = len(sig_lv); sig_lv.append(wl); sig_form.append(fw); sig_gate.append((x, y)); byform[fw] = w
            heapq.heappush(h, (sig_lv[w], rng.random(), w))
        tsig[t] = (h[0][2], const[t])
    # assemble the new circuit: original gates minus R, new XORs, target remaps
    gates = []; newid = {}
    order_old = [s for s in range(n, n + len(c.gates)) if s not in R]
    mp = {i: i for i in range(n)}
    built = {}
    def bsig(x):            # id of rebuild signal x in the new circuit
        if x in built: return built[x]
        if x < len(leaves): built[x] = mp_get(leaves[x]); return built[x]
        u, v = sig_gate[x]
        a = bsig(u); b = bsig(v)
        gates.append((XOR, a, b)); built[x] = n + len(gates) - 1
        return built[x]
    tmap = {}
    def mp_get(s):
        if s < n: return s
        if s in R:
            if s not in tmap:
                x, cst = tsig[s]
                g = bsig(x)
                if cst:
                    if x >= len(leaves):      # a new XOR root: emit an XNOR twin (the XOR dies if unused)
                        u, v = sig_gate[x]
                        gates.append((XNOR, bsig(u), bsig(v))); g = n + len(gates) - 1
                    else:
                        gates.append((NOT, g, g)); g = n + len(gates) - 1
                tmap[s] = g
            return tmap[s]
        if s not in mp:
            op, a, b = c.gates[s - n]
            aa = mp_get(a); bb = mp_get(b)
            gates.append((op, aa, bb)); mp[s] = n + len(gates) - 1
        return mp[s]
    import sys as _s
    _s.setrecursionlimit(20000)
    outs = [mp_get(o) for o in c.outputs]
    nc = core.Circuit(n, c.m, gates, outs, c.name, c.in_names, c.out_names).live()
    info = {'region_gates': len(R), 'leaves': len(leaves), 'targets': len(tg),
            'new_linear': len(sig_lv) - len(leaves), 'G_before': len(c.gates), 'G_after': len(nc.gates)}
    return nc, info


if __name__ == '__main__':
    f = sys.argv[1]; D = int(sys.argv[sys.argv.index('--cap') + 1])
    kind = sys.argv[sys.argv.index('--region') + 1] if '--region' in sys.argv else 'bottom'
    seed = int(sys.argv[sys.argv.index('--seed') + 1]) if '--seed' in sys.argv else 1
    c = core.read_ncff(f); rng = random.Random(seed)
    tab = targets.aes_sbox()
    for k in range(int(sys.argv[sys.argv.index('--reps') + 1]) if '--reps' in sys.argv else 1):
        nc, info = rebuild(c, D, kind, rng)
        m = nc.metrics()
        print(kind, info, 'G=%d GD=%d AD=%d ok=%s' % (m['G'], m['GD'], m['AD'], nc.value_table() == tab))
