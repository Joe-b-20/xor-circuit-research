#!/usr/bin/env python3
"""Build a full circuit from a front (the gates of FRONT with AND level <= AD-1) and a bottom decomposition
(free terms (L, R, w), fixed terms (= FRONT's level-1 ANDs, in gate order) with w, linear terms lin[o]),
in the qflip.py coordinates (bit 0 const, 1..8 x, 9..12 y of REF's Y basis).

Operand forms are built from the front's affine signals by a Boyar-Peralta-style greedy (exact distances
over the 2^12 linear forms, constants via XNOR), the output layer by Paar's pair merging (most frequent
pair first, ties to the earliest-arriving pair).  The result is checked on all 256 inputs.

    build.py REF FRONT DECOMP.json [--line K] [--out FILE.circ.txt]
"""
import json, random, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import bottom as BT  # noqa
import flip as FL   # noqa
from boolflux import core, targets  # noqa

AND, XOR, XNOR, NOT = 8, 6, 9, 3
AES = targets.aes_sbox()
MODEL = core.Model.load('nist')
ONES = BT.ONES


class Builder:
    def __init__(self, front_circ, Yt, rng=None):
        c = front_circ
        self.n = c.n
        self.rng = rng or random.Random(1)
        la, lg = BT.and_levels(c)
        self.AD = max(la[s] for s in c.outputs)
        keep = [j for j in range(len(c.gates)) if la[c.n + j] <= self.AD - 1]
        # front gates with AND level <= AD-1, renumbered
        self.gates = []
        self.newid = {i: i for i in range(c.n)}
        for j in keep:
            op, a, b = c.gates[j]
            self.newid[c.n + j] = c.n + len(self.gates)
            self.gates.append((op, self.newid[a], self.newid[b]))
        T = c.tables()
        self.tab = [T[i] for i in range(c.n)] + [T[c.n + j] for j in keep]
        self.lev = [0] * c.n + [lg[c.n + j] for j in keep]
        self.fixed_sig = [self.newid[c.n + j] for j in keep if c.gates[j][0] in BT.NL and la[c.n + j] == 1]
        self.B = FL.basis_for(Yt, c.n)
        self.btabs = [ONES] + [T[i] for i in range(c.n)] + list(Yt)
        # affine signals: form -> (signal, level), keep the earliest
        self.form_sig = {}
        for s, t in enumerate(self.tab):
            f = self.B.coords(t)
            if f is not None:
                if f not in self.form_sig or self.lev[s] < self.lev[self.form_sig[f]]:
                    self.form_sig[f] = s

    def add(self, op, a, b):
        ones = ONES
        t = core.op_apply(op, self.tab[a], self.tab[b], ones)
        self.gates.append((op, a, b)); self.tab.append(t)
        self.lev.append(1 + max(self.lev[a], self.lev[b]))
        s = self.n + len(self.gates) - 1
        return s

    def form_table(self, f):
        t = 0
        for k in range(13):
            if f >> k & 1: t ^= self.btabs[k]
        return t

    def build_forms(self, targets_):
        """Make a signal for every affine form in targets_ (13-bit masks).  Returns {form: signal}."""
        need = [f for f in set(targets_) if f not in self.form_sig]
        # exact complement available -> NOT gate (1)
        while need:
            avail = {}
            for f, s in self.form_sig.items():
                g = f >> 1
                if g not in avail or self.lev[s] < self.lev[avail[g]]: avail[g] = s
            # distance over linear part (12 bits) from avail: BFS
            dist = {g: 0 for g in avail}
            frontier = list(avail)
            av = list(avail)
            d = 0
            tg = set(f >> 1 for f in need)
            while not tg <= set(dist) and frontier and d < 6:
                d += 1; nf = []
                for g in frontier:
                    for h in av:
                        x = g ^ h
                        if x not in dist: dist[x] = d; nf.append(x)
                frontier = nf
            # targets at linear distance 0 (complement only) or 1: build directly
            built = False
            for f in sorted(need, key=lambda f: dist.get(f >> 1, 99)):
                g = f >> 1
                if dist.get(g, 99) == 0:
                    s = avail[g]
                    # differs only in the constant
                    s2 = self.add(NOT, s, s); self.form_sig[f] = s2; built = True; break
                if dist.get(g, 99) == 1:
                    best = None
                    for h in av:
                        if (g ^ h) in avail:
                            a, b = avail[h], avail[g ^ h]
                            L = max(self.lev[a], self.lev[b])
                            if best is None or L < best[0]: best = (L, a, b)
                    _, a, b = best
                    fa = self.B.coords(self.tab[a]); fb = self.B.coords(self.tab[b])
                    op = XOR if ((fa ^ fb) & 1) == (f & 1) else XNOR
                    s = self.add(op, a, b); self.form_sig[f] = s; built = True; break
            if not built:
                # add the pair XOR that most reduces the summed distance of the targets (BP step)
                bestv = None
                cand = [(h1, h2) for i, h1 in enumerate(av) for h2 in av[i + 1:]]
                self.rng.shuffle(cand)
                for h1, h2 in cand[:4000]:
                    x = h1 ^ h2
                    if x in avail: continue
                    score = sum(min(dist.get(g, 99), 1 + min((dist.get(g ^ x, 99) for _ in [0]), default=99))
                                for g in tg)
                    lv = max(self.lev[avail[h1]], self.lev[avail[h2]])
                    if bestv is None or (score, lv) < bestv[:2]: bestv = (score, lv, h1, h2)
                _, _, h1, h2 = bestv
                s = self.add(XOR, avail[h1], avail[h2])
                f = self.B.coords(self.tab[s]); self.form_sig[f] = s
            need = [f for f in need if f not in self.form_sig]
        return {f: self.form_sig[f] for f in targets_}

    def output_layer(self, rows, consts):
        """rows[o] = set of signals to XOR; consts[o] = 1 to complement.  Paar greedy with level tie-break."""
        rows = [set(r) for r in rows]
        while True:
            cnt = {}
            for r in rows:
                rl = sorted(r)
                for i in range(len(rl)):
                    for j in range(i + 1, len(rl)):
                        cnt[(rl[i], rl[j])] = cnt.get((rl[i], rl[j]), 0) + 1
            if not cnt: break
            m = max(cnt.values())
            cands = [p for p, v in cnt.items() if v == m]
            if m == 1:
                # no sharing left: finish each row as a Huffman tree on arrival levels
                break
            p = min(cands, key=lambda p: (max(self.lev[p[0]], self.lev[p[1]]), self.rng.random()))
            s = self.add(XOR, p[0], p[1])
            for r in rows:
                if p[0] in r and p[1] in r:
                    r.discard(p[0]); r.discard(p[1]); r.add(s)
        outs = []
        for o, r in enumerate(rows):
            r = sorted(r, key=lambda s: self.lev[s])
            while len(r) > 1:
                a, b = r[0], r[1]
                last = len(r) == 2
                op = XNOR if (last and consts[o]) else XOR
                s = self.add(op, a, b)
                r = sorted(r[2:] + [s], key=lambda s: self.lev[s])
                if last and consts[o]: consts = list(consts); consts[o] = 0
            s = r[0]
            if consts[o]:
                s = self.add(NOT, s, s)
            outs.append(s)
        return outs

    def circuit(self, outs):
        c = core.Circuit(self.n, 8, list(self.gates), outs)
        return c.live()


def build(front, Yt, free, fixed, lin, rng=None):
    bd = Builder(front, Yt, rng)
    assert len(bd.fixed_sig) == len(fixed), (len(bd.fixed_sig), len(fixed))
    forms = []
    for L, R, w in free: forms += [L, R]
    linf = [l for l in lin if l >> 1]
    fs = bd.build_forms(forms + [l & ~1 for l in linf])
    rows = [set() for _ in range(8)]
    consts = [0] * 8
    for L, R, w in free:
        s = bd.add(AND, fs[L], fs[R])
        for o in range(8):
            if w >> o & 1: rows[o] ^= {s}
    for k, (L, R, w) in enumerate(fixed):
        for o in range(8):
            if w >> o & 1: rows[o] ^= {bd.fixed_sig[k]}
    for o in range(8):
        l = lin[o]
        if l >> 1: rows[o] ^= {fs[l & ~1]}
        consts[o] = l & 1
    outs = bd.output_layer(rows, consts)
    c = bd.circuit(outs)
    return c


def main():
    a = sys.argv[1:]
    ref, front, dec = a[0], a[1], a[2]
    line = int(a[a.index('--line') + 1]) if '--line' in a else 0
    rc, Yt = FL.ref_basis(ref)
    fc = BT.load(front)
    recs = [json.loads(l) for l in open(dec)]
    r = recs[line]
    # constants: the decomposition's lin carries the constant bits
    c = build(fc, Yt, [tuple(t) for t in r['free']], [tuple(t) for t in r['fixed']], r['lin'])
    ok = c.value_table() == AES
    m = c.metrics(MODEL)
    print('ok', ok, 'A AD G GD', m['A'], m['AD'], m['G'], m['GD'])
    if '--out' in a and ok:
        Path(a[a.index('--out') + 1]).write_text(core.write_ncff(c, MODEL))


if __name__ == '__main__':
    main()
