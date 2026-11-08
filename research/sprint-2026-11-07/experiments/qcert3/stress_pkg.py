#!/usr/bin/env python3
"""Independent stress test of every circuit-level statement of the 75 proof on real circuits.

Usage: python3 stress.py [corpus_file [limit]]   (default: the circuits of this repository)

For each circuit C (records + bothforest corpus) and its canonical transpose T(C) and T(T(C)):
  identities (gate count, incidence counts, Q = 2x', origin identity, exact potential identity (E)),
  every inequality row of certify75's system evaluated with the circuit's own (h, y, F, q, z) and orientation,
  structural lemmas (simple graph, matchings, r <= 3, independence of represented relations, no adjacent full
  helpers, missing-label sets pairwise intersect in <= 1, NO_ODD_LEAVES on canonical transposes,
  x(T(T(C))) = x(C), y(T(T(C))) >= y(C), f_v formula = EE count at each accumulation).
Standard library only; nothing imported from the bundle.
"""
import sys, json, itertools, random, time
from collections import Counter, defaultdict
from math import comb
from multiprocessing import Pool

sys.setrecursionlimit(10000)
from pathlib import Path
def _repo_root():
    """The enclosing repository root: the first ancestor holding a circuits/ or evidence/circuits/ directory."""
    for d in Path(__file__).resolve().parents:
        if (d / 'circuits').is_dir() or (d / 'evidence' / 'circuits').is_dir(): return d
    return Path(__file__).resolve().parents[2]
REPO = _repo_root()

def xtime(a):
    a <<= 1
    return (a ^ 0x11B) & 0xFF if a & 0x100 else a & 0xFF
def gmul(a, b):
    r = 0
    for i in range(8):
        if (b >> i) & 1:
            t = a
            for _ in range(i): t = xtime(t)
            r ^= t
    return r & 0xFF
def mixcolumns_rows():
    coef = [2, 3, 1, 1]; rows = [0] * 32
    for col in range(4):
        for k in range(4):
            c, ib = coef[k], (col + k) % 4
            for in_bit in range(8):
                v = gmul(c, 1 << in_bit)
                for out_bit in range(8):
                    if (v >> out_bit) & 1: rows[col * 8 + out_bit] ^= 1 << (ib * 8 + in_bit)
    return rows
ROWS = mixcolumns_rows()
COLS = [sum(((ROWS[r] >> c) & 1) << r for r in range(32)) for c in range(32)]
TARGETS = {'M': ROWS, 'Mt': COLS}          # output masks of the map computed by a circuit in each orientation
BOUNDARY = {'M': [1 << i for i in range(32)] + ROWS, 'Mt': [1 << i for i in range(32)] + COLS}
def parity(m): return bin(m).count('1') & 1

def rank(vectors):
    piv = {}
    for v in vectors:
        while v:
            h = v.bit_length() - 1
            if h in piv: v ^= piv[h]
            else: piv[h] = v; break
    return len(piv)

# finite constants (recomputed independently in finite_facts.py)
RHO6 = {'M': 20, 'Mt': 28}; RESERVE = {'M': 8, 'Mt': 4}

class Circuit:
    """gates: list of (a,b) over signal indices; inputs 0..31; gate k emits 32+k. orientation: which map it computes."""
    def __init__(self, gates, orientation):
        self.gates = [tuple(g) for g in gates]; self.ori = orientation
        n = 32 + len(gates)
        self.mask = [1 << i for i in range(32)] + [0] * len(gates)
        for k, (a, b) in enumerate(self.gates):
            assert a < 32 + k and b < 32 + k and a != b
            self.mask[32 + k] = self.mask[a] ^ self.mask[b]
        self.n = n; self.G = len(gates)
        assert len(set(self.mask)) == n and all(self.mask), 'not normalized (duplicate or zero signal)'
        tgt = TARGETS[orientation]
        where = {m: i for i, m in enumerate(self.mask)}
        assert all(t in where for t in tgt), 'does not compute the map'
        self.out_index = {}            # signal -> output number j
        for j, t in enumerate(tgt): self.out_index[where[t]] = j
        self.uses = [[] for _ in range(n)]
        for k, (a, b) in enumerate(self.gates):
            self.uses[a].append(32 + k); self.uses[b].append(32 + k)
        self.d = [len(self.uses[v]) + (1 if v in self.out_index else 0) for v in range(n)]
        assert all(self.d[v] >= 1 for v in range(n)), 'dead signal'
        self.odd = [parity(m) for m in self.mask]
        assert all(self.odd[v] for v in self.out_index) and all(self.odd[i] for i in range(32))

    def analyse(self):
        """odd graph, counts, helper types, adjoints, canonical transpose data."""
        C = self; n = C.n
        B = set(range(32)) | set(C.out_index)
        H = [v for v in range(32, n) if C.odd[v] and v not in C.out_index]
        x = y = 0
        edges = []; result = {}     # (p, q, label) with p<q odd signals; result[(p,q)] = the gate's result signal
        for k, (a, b) in enumerate(C.gates):
            s = 32 + k
            if C.odd[a] and C.odd[b]: x += 1; edges.append((min(a, b), max(a, b), s)); result[(min(a, b), max(a, b))] = s
            elif not C.odd[a] and not C.odd[b]: y += 1
            else:
                o, e = (a, b) if C.odd[a] else (b, a)
                edges.append((min(o, s), max(o, s), e)); result[(min(o, s), max(o, s))] = s
        h = len(H)
        assert C.G == 32 + x + y + h
        assert len({(p, q) for p, q, _ in edges}) == len(edges), 'odd graph not simple'
        bylabel = defaultdict(list)
        for p, q, e in edges: bylabel[e].append((p, q))
        for e, es in bylabel.items():
            verts = [v for pq in es for v in pq]
            assert len(verts) == len(set(verts)), 'label not a matching'
        evens = [v for v in range(32, n) if not C.odd[v]]
        assert len(evens) == x + y
        bb_label = {}
        for e in evens:
            bb = [(p, q) for p, q in bylabel.get(e, []) if p in B and q in B]
            assert len(bb) <= 1, 'two B-B edges with one label (Sidon violated?)'
            if bb: bb_label[e] = bb[0]
        q = len(evens) - len(bb_label)
        z = sum(1 for p, qq, _ in edges if p not in B and qq not in B)
        HB = sum(1 for p, qq, _ in edges if (p in B) != (qq in B))
        assert HB == 32 + h - y + q - z
        assert sum(C.d[v] for v in H) == 32 - y + q + z
        assert 32 <= 2 * h + y + z + comb(q, 2), 'incidence inequality violated'
        # helper types
        types = {}; missing_sets = {}; rep_rows = []; missing_rows = []
        Bidx = {v: i for i, v in enumerate(sorted(B))}     # formal boundary coordinates 0..63
        Hidx = {v: i for i, v in enumerate(H)}
        for v in H:
            r = u = vv = 0; ms = set()
            for p, qq, e in edges:
                if v not in (p, qq): continue
                w = qq if p == v else p
                if w in B:
                    if e in bb_label:
                        r += 1
                        b1, b2 = bb_label[e]
                        T = (1 << Bidx[w]) | (1 << Bidx[b1]) | (1 << Bidx[b2])
                        assert w not in (b1, b2)
                        rep_rows.append(T | (1 << (64 + Hidx[v])))
                        assert C.mask[v] == C.mask[w] ^ C.mask[b1] ^ C.mask[b2]
                    else:
                        u += 1; ms.add(e)
                        missing_rows.append((1 << Bidx[w]) | (1 << (64 + Hidx[v])) | (1 << (64 + h + evens.index(e))))
                else: vv += 1
            assert r <= 3
            types[v] = (r, u, vv); missing_sets[v] = ms
            assert r + u + vv == C.d[v] + 1
        assert rank(rep_rows) == len(rep_rows), 'represented relations dependent'
        assert rank(rep_rows + missing_rows) == len(rep_rows) + len(missing_rows)
        for v1, v2 in itertools.combinations(H, 2):
            assert len(missing_sets[v1] & missing_sets[v2]) <= 1, 'two helpers share two missing labels'
            if types[v1][0] == 3 and types[v2][0] == 3:
                assert (C.mask[v1] ^ C.mask[v2]) not in PAIRVALS[C.ori], 'adjacent full helpers'
        # adjoints over the 32 terminal variables z_j (adjoint of output j includes z_j)
        adj = [0] * n
        for v in range(n - 1, -1, -1):
            a = 0
            for w in C.uses[v]: a ^= adj[w]
            if v in C.out_index: a ^= 1 << C.out_index[v]
            adj[v] = a
        tgt_other = TARGETS['Mt' if C.ori == 'M' else 'M']
        assert all(adj[i] == tgt_other[i] for i in range(32)), 'input adjoints are not the rows of the transpose'
        k = [0] * n; f = [0] * n
        for v in range(n):
            contrib = [parity(adj[w]) for w in C.uses[v]] + ([1] if v in C.out_index else [])
            k[v] = sum(contrib)
            assert (k[v] & 1) == parity(adj[v])
            f[v] = max(0, C.d[v] - (k[v] + 1) // 2 - 1)
            assert C.d[v] <= 3 + 2 * f[v]
        Q = sum(parity(adj[v]) for v in range(32, n))
        assert sum(k) == 2 * Q + 32 and sum(parity(adj[v]) for v in range(n)) == Q + 32
        xprime = sum(kv // 2 for kv in k)
        assert 2 * xprime == Q
        e1 = sum(1 for kk, (a, b) in enumerate(C.gates) if not C.odd[a] and not C.odd[b] and parity(adj[32 + kk]))
        F = sum(f); F_H = sum(f[v] for v in H); F_B = sum(f[v] for v in B)
        L_H = sum(1 for v in H if C.d[v] == 1 and k[v] == 1)
        E_B = sum(max(0, C.d[v] - 2) for v in B)
        s = q + z
        # weighted-degree ledger (A): 2x' >= 32 + sum_H ceil(k/2) + e1, and (B)
        wdeg = Counter()
        for p, qq, e in edges:
            wt = parity(adj[result[(p, qq)]]); wdeg[p] += wt; wdeg[qq] += wt   # weight = adjoint parity of the gate's result
        assert all(wdeg[v] % 2 == 1 for v in B), 'boundary weighted degree not odd'
        for v in H: assert wdeg[v] == 2 * ((k[v] + 1) // 2)
        assert sum(wdeg.values()) == 2 * (Q - e1)
        assert 2 * xprime >= 32 + sum((k[v] + 1) // 2 for v in H) + e1
        assert 2 * xprime + h + y + F_H >= 64 + s + e1
        # exact boundary identity: sum_B (wdeg-1)/2 + F_B + L_H = E_B
        assert sum((wdeg[v] - 1) // 2 for v in B) + F_B == E_B
        return dict(x=x, y=y, h=h, q=q, z=z, s=s, F=F, F_H=F_H, F_B=F_B, e1=e1, xprime=xprime, E_B=E_B, L_H=L_H,
                    types=Counter(types.values()), adj=adj, k=k, f=f, H=H, B=B, Q=Q)

    def canonical_transpose(self, info, rng=None):
        """Build T(C) with the canonical association. Returns (Circuit of the other orientation, origin list)."""
        C = self; n = C.n; adj = info['adj']
        # signals of T: 0..31 = z_j ; then gates.  sig_of[v] = T-signal carrying a(v)
        tg = []; origin = []            # origin[k] = original signal whose accumulation created gate k of T
        sig_of = [None] * n
        tmask = [1 << j for j in range(32)]
        def new_gate(a, b, v):
            tg.append((a, b)); origin.append(v); tmask.append(tmask[a] ^ tmask[b]); return 32 + len(tg) - 1
        for v in range(n - 1, -1, -1):
            items = [sig_of[w] for w in C.uses[v]]
            if v in C.out_index: items.append(C.out_index[v])
            if rng: rng.shuffle(items)
            odd = [t for t in items if parity(tmask[t])]; even = [t for t in items if not parity(tmask[t])]
            assert len(odd) == info['k'][v]
            ee = 0
            evens = list(even)
            while len(odd) >= 2:
                a, b = odd.pop(), odd.pop(); evens.append(new_gate(a, b, v))
            acc = None
            for t in evens:
                if acc is None: acc = t
                else: acc = new_gate(acc, t, v); ee += 1
            if odd:
                acc = odd[0] if acc is None else new_gate(acc, odd[0], v)
            assert ee == info['f'][v], (v, ee, info['f'][v])
            sig_of[v] = acc
            assert tmask[acc] == adj[v]
        assert len(tg) == C.G
        T = Circuit(tg, 'Mt' if C.ori == 'M' else 'M')
        # the outputs of T are a(input_i): check they are the targets in order
        for i in range(32): assert T.mask[sig_of[i]] == TARGETS[T.ori][i]
        return T, origin

def check_rows(info, ori):
    """Every inequality of certify75.system() evaluated for the circuit's own counts; returns min slack per row."""
    h, y, F, q, z = info['h'], info['y'], info['F'], info['q'], info['z']
    types = info['types']
    def S(fn): return sum(fn(r, u, v) * c for (r, u, v), c in types.items())
    def f(r, u, v): return max(0, (r + u + v - 3) // 2)
    def deficit(r, u): return u - 1 if r == 0 else 0
    def overflow(r, u): return max(0, u - 2) if r == 3 else 0
    rho = RHO6[ori]; res = RESERVE[ori]
    rows = {
        'reverse EE budget': F - S(f),
        'missing pairs': comb(q, 2) - S(lambda r, u, v: comb(u, 2)),
        'full missing incidence': q - S(lambda r, u, v: u if r == 3 else 0),
        'label rank capacity': 7 * q - S(lambda r, u, v: r * u),
        'full helper budget': 3 * h + 2 * F + y - 32 - S(lambda r, u, v: 1 + 2 * f(r, u, v) if r == 3 else 0),
        'weighted label capacity': 3 * q - S(lambda r, u, v: max(0, r - 1) * u),
        'even signal fanout': 4 * q + 2 * F - S(lambda r, u, v: u + 2 * f(r, u, v)),
        'full helper incidence': q + z - S(lambda r, u, v: u + v if r == 3 else 0),
        'boundary R6 rank': rho - S(lambda r, u, v: max(0, r - 1)),
        'quotient rank capacity': 2 * y + 2 * z + 7 * q - 2 * res - S(lambda r, u, v: r * u - 2 * deficit(r, u)),
        'quotient full capacity': 2 * y + 2 * z + 7 * q - 2 * res + (2 if ori == 'M' else 0) - S(lambda r, u, v: r * u + (u if r == 3 else 0) - 2 * deficit(r, u)),
        'quotient excess capacity': y + z + 3 * q - res - S(lambda r, u, v: max(0, r - 1) * u - deficit(r, u)),
        'full excess overflow': 3 * q - S(lambda r, u, v: max(0, r - 1) * u + overflow(r, u)),
        'fanout cap s<=3h+2F+y-32': 3 * h + 2 * F + y - 32 - (q + z),
        'incidence 32<=2h+y+z+C(q,2)': 2 * h + y + z + comb(q, 2) - 32,
        'helper degree >= 2 (any circuit)': min((r + u + v for (r, u, v) in types), default=99) - 2,
    }
    if ori == 'M':
        rows['quotient joint deficit'] = 3 * y + 3 * z + 6 * q - 24 - S(lambda r, u, v: 2 * max(0, r - 1) * u + 2 * overflow(r, u) - 3 * deficit(r, u))
    else:
        rows['quotient joint deficit'] = 3 * y + 3 * z + 3 * q - 12 - S(lambda r, u, v: max(0, r - 1) * u + overflow(r, u) - 3 * deficit(r, u))
        rows['quotient full strengthened'] = 3 * y + 3 * z + 7 * q - 12 - S(lambda r, u, v: r * u + (u if r == 3 else 0) - 3 * deficit(r, u))
        rows['dark repeated pairs'] = y - 3 - S(lambda r, u, v: -(u + v - 1) if r == 0 else (-v if r == 1 else 0))
        rows['dark quotient rank'] = 3 * y + 2 * z - 9 - S(lambda r, u, v: -(3 * u + v - 3) if r == 0 else 0)
        if q == 0:
            rows['unanchored required'] = -1 - S(lambda r, u, v: -int(r == 0))
            rows['short boundary rank'] = y - 3 - S(lambda r, u, v: -(v - 1) if r == 0 else 0)
            rows['Mt q=0 => z>=8 (canonical only)'] = z - 8
    if q == 6: rows['six color packing'] = 4 - S(lambda r, u, v: {3: 1, 4: 3, 5: 4, 6: 4}.get(u, 0))
    if q == 7: rows['seven color packing'] = 14 - S(lambda r, u, v: {3: 2, 4: 7, 5: 12, 6: 14, 7: 14}.get(u, 0))
    rows['q=z=0 never'] = (q + z) - 1
    return rows

PAIRVALS = {o: {a ^ b for a, b in itertools.combinations(BOUNDARY[o], 2)} for o in BOUNDARY}

def process(args):
    tag, gates, ori = args
    out = {'tag': tag, 'ok': True, 'min_slack': {}, 'facts': {}}
    try:
        C = Circuit(gates, ori); I = C.analyse()
        T, origin = C.canonical_transpose(I); J = T.analyse()
        T2, origin2 = T.canonical_transpose(J); K = T2.analyse()
        # origin identity: adjoint (in T) of every gate of T equals the mask of its origin in C; e(T(C)) = sum_{v odd} f_v
        assert all(J['adj'][32 + k] == C.mask[origin[k]] for k in range(T.G)), 'origin identity'
        assert J['e1'] == sum(I['f'][v] for v in range(C.n) if C.odd[v])
        assert J['x'] == I['xprime'] and J['y'] == I['F']
        assert K['x'] == I['x'], 'x(T(T(C))) != x(C)'
        assert K['y'] >= I['y'], 'y(T(T(C))) < y(C)'
        # NO_ODD_LEAVES on T(C) and T(T(C)): helper fan-out >= 2
        assert all(T.d[v] >= 2 for v in J['H']), 'odd helper leaf in canonical transpose'
        assert all(T2.d[v] >= 2 for v in K['H'])
        # exact potential identity (E): e(T(C)) - e(C) = s + 96 - G + x - 2x' + E_B + L_H
        assert J['e1'] - I['e1'] == I['s'] + 96 - C.G + I['x'] - 2 * I['xprime'] + I['E_B'] + I['L_H'], 'identity (E)'
        assert K['e1'] - J['e1'] == J['s'] + 96 - T.G + J['x'] - 2 * J['xprime'] + J['E_B'] + J['L_H']
        # h(T) = 2 x(T) - #{signals of C with odd adjoint and fan-out 1}
        L1 = sum(1 for v in range(C.n) if C.d[v] == 1 and parity(I['adj'][v]))
        assert J['h'] == 2 * J['x'] - L1
        for name, info, circ in (('C', I, C), ('TC', J, T), ('TTC', K, T2)):
            rows = check_rows(info, circ.ori)
            for rname, sl in rows.items():
                key = f'{name}:{circ.ori}:{rname}'
                assert sl >= 0, f'ROW VIOLATED {key} slack {sl}'
                out['min_slack'][key] = sl
        out['facts'] = dict(x=I['x'], y=I['y'], h=I['h'], q=I['q'], z=I['z'], xp=I['xprime'], F=I['F'], e1=I['e1'],
                            E_B=I['E_B'], L_H=I['L_H'], xT=J['x'], yT=J['y'], hT=J['h'], qT=J['q'], zT=J['z'], E_BT=J['E_B'],
                            yTT=K['y'], ident_budget=I['s'] + J['s'] + 192 - 2 * C.G - I['x'] - J['x'] + I['E_B'] + J['E_B'] + I['L_H'] + J['L_H'] - (K['e1'] - I['e1']))
    except AssertionError as ex:
        out['ok'] = False; out['error'] = str(ex) or repr(ex)
    return out

def load_jobs(corpus=None, limit=None):
    """The circuits of the enclosing repository (circuits/*.json or evidence/circuits/*.json), plus an optional corpus file (one circuit per line:
    an id followed by 88 'a,b' pairs), optionally limited to the first `limit` lines."""
    jobs = []
    import glob, os
    for fn in sorted(glob.glob(str(REPO / 'circuits' / '*.json')) + glob.glob(str(REPO / 'evidence' / 'circuits' / '*.json'))):
        d = json.load(open(fn))
        g = d['gates'] if isinstance(d, dict) else d
        if g and isinstance(g[0], list) and len(g[0]) == 2: jobs.append((os.path.basename(fn), g, 'M'))
    if corpus:
        with open(corpus) as fh:
            for ln, line in enumerate(fh):
                toks = line.split()
                pairs = [tuple(map(int, t.split(','))) for t in toks if ',' in t]
                if len(pairs) >= 60: jobs.append((f'corpus:{ln}', pairs, 'M'))
                if limit and ln + 1 >= limit: break
    return jobs

if __name__ == '__main__':
    corpus = sys.argv[1] if len(sys.argv) > 1 else None
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    jobs = load_jobs(corpus, limit)
    print('jobs', len(jobs), flush=True)
    t0 = time.time(); bad = []; mins = {}; n = 0; facts_hist = Counter()
    with Pool(5) as pool:
        for out in pool.imap_unordered(process, jobs, chunksize=20):
            n += 1
            if not out['ok']: bad.append((out['tag'], out['error'])); print('FAIL', out['tag'], out['error'], flush=True)
            for kk, v in out['min_slack'].items():
                mins[kk] = min(mins.get(kk, 10 ** 9), v)
            fa = out.get('facts')
            if fa: facts_hist[(fa['x'], fa['xT'], fa['y'], fa['yT'], fa['yTT'] >= fa['y'], fa['ident_budget'])] += 1
            if n % 2000 == 0: print(f'{n} done, {len(bad)} failures, {time.time()-t0:.0f}s', flush=True)
    rep = {'circuits': n, 'failures': bad, 'min_slack': dict(sorted(mins.items())), 'facts_hist_top': facts_hist.most_common(12)}
    json.dump(rep, open(__file__.replace('.py', '.json'), 'w'), indent=1, default=str)
    print(json.dumps(rep, indent=1, default=str))
    if bad or n == 0:
        print(f'STRESS TEST FAILED: {len(bad)} failing circuits, {n} tested', file=sys.stderr)
        sys.exit(1)
    print(f'STRESS TEST PASSED: {n} circuits, 0 failures')
