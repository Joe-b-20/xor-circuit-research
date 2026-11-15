#!/usr/bin/env python3
"""P7: T10 at GD10 over the 2040 GF(2^8)-inversion conjugates of NIST 59@10.

Conjugation (idea and the naive conjugate construction copied from strategies/P3/conj.py, coordinator
tip 2026-11-15): S(x) = Mout (S(G x) + c) + c, G(z) = lam z^(2^k).  The conjugate keeps the inversion
(4 N-coordinates -> 4 base Y-forms) but its N-coordinates become other quadratic forms of x and its
Y-forms another basis of Tr(alpha N^-1).  For each (lam, k):
  1. screen: number of 4-product decompositions (<= 2-variable operands, gate level 2) of each
     N-coordinate (all four must have one, or the 3+2 shape) and the bottom's new x-forms in the
     conjugate's own Y-basis (xcount model);
  2. build (for promising ones): regroup.py all four groups with each decomposition choice
     (s1pol enumeration), then a GD10 bottom (forced base decomposition) with bbuild.py.
    t10conj.py screen OUT.jsonl [--lams 1-255] [--ks 0-7]
    t10conj.py build LAM K OUTDIR
"""
import itertools, json, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s1lib as L  # noqa: E402
import s1search, bsel, bopt  # noqa: E402
from boolflux import targets  # noqa: E402
core = L.core
AND, XOR, XNOR, NOT = 8, 6, 9, 3
AES = targets.aes_sbox()
MODEL = core.Model.load(str(core.MODELS / 'nist.json'))
REF = Path.home() / 'xcr-boolflux/nonlinear/nist/aes-sbox/aes-sbox-a59-ad4-g159-gd10-xxn100-30-3.circ.txt'


# ---- copied from strategies/P3/conj.py (P3, 2026-11-15) ----
def gmul(a, b):
    r = 0
    while b:
        if b & 1: r ^= a
        a <<= 1
        if a & 0x100: a ^= 0x11B
        b >>= 1
    return r


def gpow(a, e):
    r = 1
    while e:
        if e & 1: r = gmul(r, a)
        a = gmul(a, a); e >>= 1
    return r


def matrix(f): return [f(1 << j) for j in range(8)]


def apply(M, x):
    r = 0
    for j in range(8):
        if x >> j & 1: r ^= M[j]
    return r


INV = [0] + [gpow(z, 254) for z in range(1, 256)]
A_ = matrix(lambda w: AES[INV[w]] ^ 0x63)
Ainv = [0] * 8
for y in range(256):
    v = apply(A_, y)
    for j in range(8):
        if v == 1 << j: Ainv[j] = y


def conj_circuit(c, lam, k):
    G = matrix(lambda z: gmul(lam, gpow(z, 1 << k)))
    Gp = matrix(lambda w: gpow(gmul(lam, w), 1 << ((8 - k) % 8)))
    Mout = matrix(lambda y: apply(A_, apply(Gp, apply(Ainv, y))))
    const = apply(Mout, 0x63) ^ 0x63
    n = c.n; gates = []
    def sid(): return n + len(gates) - 1
    u = []
    for i in range(8):
        bit = 7 - i
        terms = [7 - j for j in range(8) if G[j] >> bit & 1]
        s = terms[0]
        for t in terms[1:]:
            gates.append((XOR, s, t)); s = sid()
        u.append(s)
    mp = {i: u[i] for i in range(n)}
    for j, (op, a, b) in enumerate(c.gates):
        gates.append((op, mp[a], mp[b])); mp[n + j] = sid()
    old = [mp[s] for s in c.outputs]
    outs = []
    for i in range(8):
        bit = 7 - i
        terms = [old[7 - j] for j in range(8) if Mout[j] >> bit & 1]
        cst = const >> bit & 1
        s = terms[0]
        for q, t in enumerate(terms[1:]):
            last = q == len(terms) - 2
            gates.append((XNOR if (last and cst) else XOR, s, t)); s = sid()
        if cst and len(terms) == 1:
            gates.append((NOT, s, s)); s = sid()
        outs.append(s)
    return core.Circuit(n, 8, gates, outs).live()
# ---- end of copy ----


P2 = None; W2 = None


def prep():
    global P2, W2
    forms = [m for m in range(1, 256) if bin(m).count('1') <= 2]
    P2 = [(l, m, L.wedge(l, m)) for l, m in itertools.combinations(forms, 2) if L.wedge(l, m)]
    W2 = {}
    for i1 in range(len(P2)):
        for i2 in range(i1 + 1, len(P2)):
            W2.setdefault(P2[i1][2] ^ P2[i2][2], []).append((i1, i2))


def n4(q):
    cnt = 0
    for i1 in range(len(P2)):
        for i2 in range(i1 + 1, len(P2)):
            for (i3, i4) in W2.get(q ^ P2[i1][2] ^ P2[i2][2], ()):
                if i3 > i2: cnt += 1
    return cnt


def screen(out, lams, ks):
    prep()
    c0 = L.load(str(REF))
    fo = open(out, 'a')
    for lam in lams:
        for k in ks:
            t0 = time.time()
            cc = conj_circuit(c0, lam, k)
            fs, T, lg, la = s1search.coords(cc)
            cnt = [n4(L.quad(f)) for f in fs]
            T2, lg2, la2, Ys, Ylev = bsel.front_info(cc)
            try:
                U, C = bsel.decompose_outputs(cc, T2, Ys)
                ws = set(w for u in U for w in u)
                nx = sum(1 for w in ws if bin(w).count('1') > 1)
            except Exception:
                nx = -1
            rec = {'lam': lam, 'k': k, 'n4': cnt, 'xforms': nx, 's': round(time.time() - t0, 2)}
            fo.write(json.dumps(rec) + '\n'); fo.flush()


def bottom10(c):
    """replace the bottom by a GD10 rank-1 bottom over the 4 raw base Y signals (forced decomposition)."""
    from bbuild import Net, bp_synth
    n = c.n
    T, lg, la = L.sim(c)
    Ysig = []
    for j, (op, a, b) in enumerate(c.gates):
        s = n + j
        if op in core.NONLINEAR_OPS and la[s] == 4:
            for o in (a, b):
                if L.deg(T[o]) > 1 and o not in Ysig: Ysig.append(o)
    Ysig.sort(key=lambda s: lg[s])
    base = []
    for s in Ysig:
        if bsel.gauss_solve([T[b] for b in base], T[s]) is None: base.append(s)
        if len(base) == 4: break
    basis = [T[y] & L.VAR[l] for y in base for l in range(8)] + [L.ONES]
    U = []; C = []
    for o in c.outputs:
        sol = bsel.gauss_solve(basis, T[o])
        if sol is None: return None
        u = [0] * 4; cst = 0
        for k in sol:
            if k == 32: cst = 1
            else: u[k // 8] |= 1 << (k % 8)
        U.append(u); C.append(cst)
    net = Net(c)
    cone = set(); st = list(base)
    while st:
        x = st.pop()
        if x < n or x in cone: continue
        cone.add(x); op, a, b = c.gates[x - n]; st += [a, b]
    avail = {1 << i: i for i in range(n)}
    for s in cone:
        if c.gates[s - n][0] not in core.NONLINEAR_OPS and la[s] == 0:
            m = bopt.mask_of(T[s])
            if m is not None and (m not in avail or (T[s] & 1 == 0 and net.tab[avail[m]] & 1)): avail[m] = s
    need = {w for u in U for w in u if w}
    bp_synth(net, avail, need)
    for w in need:
        sg = avail[w]
        if net.tab[sg] & 1:
            op, a, b = net.nodes[sg]
            avail[w] = net.add(XNOR if op == XOR else XOR, a, b) if op in (XOR, XNOR) else net.add(NOT, sg, sg)
    prod = {}
    outs = []
    for j, u in enumerate(U):
        terms = []
        for i in range(4):
            if u[i]:
                key = (i, u[i])
                if key not in prod: prod[key] = net.add(AND, base[i], avail[u[i]])
                terms.append(prod[key])
        while len(terms) > 1:
            terms.sort(key=lambda s: net.lev[s])
            a = terms.pop(0); b = terms.pop(0); terms.append(net.add(XOR, a, b))
        s = terms[0]
        if net.tab[s] != T[c.outputs[j]]:
            op, a, b = net.nodes[s]; net.nodes[s] = (XNOR if op == XOR else XOR, a, b); net.tab[s] ^= L.ONES
        outs.append(s)
    return net.emit(outs)


def build(lam, k, outdir, maxcomb=300):
    import random, subprocess, regroup, rgscan
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    c0 = L.load(str(REF))
    cc = conj_circuit(c0, lam, k)
    f = outdir / ('cj-%d-%d.circ.txt' % (lam, k))
    f.write_text(core.write_ncff(cc, MODEL))
    subprocess.run(['python3', str(HERE / 's1pol.py'), str(f)], capture_output=True, text=True)
    D = json.load(open(Path.home() / 'xs-campaigns/2026-11-15-targets/P7/runs/s1' / ('alldec-%s.json' % f.name.split('.')[0])))
    fs = [int(x, 16) for x in D['fs']]; decs = D['decs']
    print('lam %d k %d decompositions per coordinate' % (lam, k), [len(d) for d in decs], flush=True)
    if any(len(d) == 0 for d in decs): return None
    combos = list(itertools.product(*[range(len(d)) for d in decs]))
    random.Random(lam * 8 + k).shuffle(combos)
    best = None
    for ch in combos[:maxcomb]:
        c = cc
        try:
            for kk, i in enumerate(ch):
                ss = rgscan.sumsigs(c, fs[kk])
                c = regroup.build(c, ss, [(l, a, m, b) for (l, a, m, b, g) in decs[kk][i]])
            c = bottom10(c)
        except Exception as e:
            continue
        if c is None or c.value_table() != AES: continue
        m = c.metrics(MODEL)
        if best is None or (m['GD'] > 10, m['G']) < (best[0]['GD'] > 10, best[0]['G']):
            best = (m, c, ch)
            print('  combo %s: %d/%d/%d/%d' % (ch, m['A'], m['AD'], m['G'], m['GD']), flush=True)
    if best:
        m, c, ch = best
        p = outdir / ('cjb-%d-%d-a%d-g%d-gd%d.circ.txt' % (lam, k, m['A'], m['G'], m['GD']))
        p.write_text(core.write_ncff(c, MODEL, comments=['P7 t10conj.py build lam %d k %d combo %s' % (lam, k, ch)]))
        print('BEST', lam, k, '%d/%d/%d/%d' % (m['A'], m['AD'], m['G'], m['GD']), p)
    return best


def main():
    if sys.argv[1] == 'screen':
        lo, hi = [int(x) for x in (sys.argv[sys.argv.index('--lams') + 1] if '--lams' in sys.argv else '1-255').split('-')]
        klo, khi = [int(x) for x in (sys.argv[sys.argv.index('--ks') + 1] if '--ks' in sys.argv else '0-7').split('-')]
        screen(sys.argv[2], range(lo, hi + 1), range(klo, khi + 1))
    elif sys.argv[1] == 'build':
        for spec in sys.argv[3:]:
            lam, k = [int(x) for x in spec.split(',')]
            build(lam, k, sys.argv[2])


if __name__ == '__main__':
    main()
