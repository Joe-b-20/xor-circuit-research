"""Reviewer's independent library (does not import mirror.py, pathstats.py, qm.py or mc.py).

Pair problem: sheets j, k = j+1 with own blocks b = block j, b' = block k, free block a = block j-1.
Local values are 12-bit: bits 0-3 block a (free), bits 4-7 block b, bits 8-11 block b'.
Own unit u (0..7): u < 4 is unit u of b, u >= 4 is unit u-4 of b'; local value 1 << (4 + u).
Mirror T: inputs 0..3 = w_c (targets (j,c)), 4..7 = w'_c (targets (k,c)); T masks are 8-bit,
omega = mask & 15, s = mask >> 4.
Standard library only.
"""
import itertools
import os
import random
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
QDIR = os.path.join(HERE, "..", "rotation", "circuits")
MCDIR = os.path.join(ROOT, "circuits", "aes-mixcolumns")


def popc(v):
    return bin(v).count("1")


def E4(c):
    return 15 ^ (1 << (c % 4))


def S4(c):
    return (1 << (c % 4)) | (1 << ((c + 1) % 4))


# ------------------------------------------------------------------ models
def qm_model(m):
    def idx(c, j):
        return 4 * (j % m) + (c % 4)
    rows = {}
    for j in range(m):
        for c in range(4):
            v = 0
            for k in range(4):
                if k != c:
                    v ^= 1 << idx(k, j)
            v ^= (1 << idx(c, j - 1)) ^ (1 << idx(c + 1, j - 1))
            rows[(c, j)] = v
    return dict(n=4 * m, m=m, idx=idx, rows=rows, name="Q%d" % m)


def mc_model():
    toks = open(os.path.join(MCDIR, "aes-mixcolumns.mat.txt")).read().split()
    r, cc = int(toks[1]), int(toks[2])
    bits = [int(t) for t in toks[3:3 + r * cc]]
    T = [sum(bits[i * cc + j] << j for j in range(cc)) for i in range(r)]

    def idx(c, j):
        return 8 * (c % 4) + (j % 8)
    rows = {(c, j): T[8 * c + j] for c in range(4) for j in range(8)}
    return dict(n=32, m=8, idx=idx, rows=rows, name="MC")


def nib(model, v, j):
    idx = model["idx"]
    return sum(((v >> idx(c, j)) & 1) << c for c in range(4))


def support(model, v):
    return frozenset(j for j in range(model["m"]) if nib(model, v, j))


# ------------------------------------------------------------------ circuits
def read_qm(path):
    ls = [l.split("#")[0].strip() for l in open(path)]
    ls = [l for l in ls if l]
    n, k = map(int, ls[0].split())
    g = [tuple(map(int, l.split()[:2])) for l in ls[1:1 + k]]
    assert len(g) == k
    return n, g


def read_ncff(path):
    idx, gates = {}, []
    for line in open(path):
        line = line.split("%")[0].strip()
        mm = re.match(r"^Inputs:\s*([a-z]+)(\d+):[a-z]+(\d+)", line)
        if mm:
            for i in range(int(mm.group(2)), int(mm.group(3)) + 1):
                idx[mm.group(1) + str(i)] = i - int(mm.group(2))
            continue
        mm = re.match(r"^XOR\s+(\S+)\s+(\S+)\s+(\S+)", line)
        if mm:
            o, a, b = mm.groups()
            gates.append((idx[a], idx[b]))
            idx[o] = 32 + len(gates) - 1
    return 32, gates


def values(n, gates):
    v = [1 << i for i in range(n)]
    for a, b in gates:
        assert a < len(v) and b < len(v)
        v.append(v[a] ^ v[b])
    return v


def computes(model, n, gates):
    vs = set(values(n, gates)[n:])
    return all(t in vs for t in model["rows"].values())


# ------------------------------------------------------------------ linear algebra
def reduce_basis(vecs):
    basis = {}
    for v in vecs:
        while v:
            h = v.bit_length() - 1
            if h in basis:
                v ^= basis[h]
            else:
                basis[h] = v
                break
    return basis


def inspan(basis, v):
    while v:
        h = v.bit_length() - 1
        if h not in basis:
            return False
        v ^= basis[h]
    return True


# ------------------------------------------------------------------ pair restriction
def pair_restricts(model, j):
    """Does the restriction to blocks j-1, j, j+1 give exactly the pair problem?"""
    m = model["m"]
    k, a = (j + 1) % m, (j - 1) % m
    bad = []
    for c in range(4):
        tj, tk = model["rows"][(c, j)], model["rows"][(c, k)]
        if (nib(model, tj, j), nib(model, tj, a), nib(model, tj, k)) != (E4(c), S4(c), 0):
            bad.append(("sheet j", c, nib(model, tj, j), nib(model, tj, a), nib(model, tj, k)))
        if (nib(model, tk, k), nib(model, tk, j), nib(model, tk, a)) != (E4(c), S4(c), 0):
            bad.append(("sheet j+1", c, nib(model, tk, k), nib(model, tk, j), nib(model, tk, a)))
    return bad


def pair_targets_local():
    return [(E4(c) << 4) | S4(c) for c in range(4)] + [(E4(c) << 8) | (S4(c) << 4) for c in range(4)]


def local_pair(model, n, gates, j, pick="first", rng=None):
    """Cut out the local pair circuit D from a full circuit (all gates that are ancestors-or-equal of the chosen
    output gates and nonzero on block j or j+1).  Operands: ('u', u), ('f', vec on a), ('g', local index)."""
    m = model["m"]
    k, a = (j + 1) % m, (j - 1) % m
    vals = values(n, gates)
    lv = [nib(model, v, a) | (nib(model, v, j) << 4) | (nib(model, v, k) << 8) for v in vals]
    tv = [model["rows"][(c, j)] for c in range(4)] + [model["rows"][(c, k)] for c in range(4)]
    outg = []
    for t in tv:
        cands = [i for i in range(n, len(vals)) if vals[i] == t]
        outg.append(cands[0] if pick == "first" else rng.choice(cands))
    anc, st = set(), list(outg)
    while st:
        s = st.pop()
        if s < n or s in anc:
            continue
        anc.add(s)
        st.extend(gates[s - n])
    D = sorted(g for g in anc if lv[g] >> 4)
    pos = {g: i for i, g in enumerate(D)}
    unit = {}
    for c in range(4):
        unit[model["idx"](c, j)] = c
        unit[model["idx"](c, k)] = 4 + c
    lc = []
    for g in D:
        ops = []
        for o in gates[g - n]:
            if o in pos:
                ops.append(("g", pos[o]))
            elif o < n and o in unit:
                ops.append(("u", unit[o]))
            else:
                assert lv[o] >> 4 == 0, "operand outside D with own part"
                ops.append(("f", lv[o] & 15))
        lc.append(tuple(ops))
    tg = [pos[t] for t in outg]
    assert [lval(lc)[t] for t in tg] == pair_targets_local()
    return lc, tg


def opval(o, v):
    if o[0] == "u":
        return 1 << (4 + o[1])
    if o[0] == "f":
        return o[1]
    return v[o[1]]


def lval(lc):
    v = []
    for a, b in lc:
        v.append(opval(a, v) ^ opval(b, v))
    return v


def clean(lc, tg):
    """Step 0: gates with two free operands become free values; keep ancestors-or-equal of the target gates."""
    status, newops = [], []
    for a, b in lc:
        ops = []
        for o in (a, b):
            if o[0] == "g" and status[o[1]] is not None:
                o = status[o[1]]
            ops.append(o)
        if ops[0][0] == "f" and ops[1][0] == "f":
            status.append(("f", ops[0][1] ^ ops[1][1]))
            newops.append(None)
        else:
            status.append(None)
            newops.append(tuple(ops))
    for t in tg:
        assert status[t] is None
    anc, st = set(), list(tg)
    while st:
        s = st.pop()
        if s in anc:
            continue
        anc.add(s)
        for o in newops[s]:
            if o[0] == "g":
                st.append(o[1])
    keep = sorted(anc)
    pos = {g: i for i, g in enumerate(keep)}
    out = [tuple(("g", pos[o[1]]) if o[0] == "g" else o for o in newops[g]) for g in keep]
    return out, [pos[t] for t in tg]


# ------------------------------------------------------------------ mirror
def level_pair(mask):
    return 0 if mask & 15 else (1 if mask else 2)


def mirror(lc, tg, order="fixed", rng=None):
    """Steps 1-3 (formal inputs, transposition).  Returns T as masks and operand pairs (T signal ids)."""
    K = len(lc)
    phi, fops = [], []
    for a, b in lc:
        ops = [a, b]
        nf = sum(1 for o in ops if o[0] == "f")
        assert nf <= 1
        if nf == 1:
            p = 0 if ops[0][0] == "f" else 1
            phi.append(ops[p][1])
            ops[p] = ("z", len(phi) - 1)
        fops.append(tuple(ops))
    tau = len(phi)
    beta, nm = [], []
    for a, b in fops:
        bb = nn = 0
        for o in (a, b):
            if o[0] == "u":
                bb ^= 1 << o[1]
            elif o[0] == "z":
                nn ^= 1 << o[1]
            else:
                bb ^= beta[o[1]]
                nn ^= nm[o[1]]
        beta.append(bb)
        nm.append(nn)
    v = lval(lc)
    for i in range(K):
        fv = 0
        for t in range(tau):
            if (nm[i] >> t) & 1:
                fv ^= phi[t]
        assert v[i] == ((beta[i] << 4) | fv)
    readers = {}
    for i, ops in enumerate(fops):
        for o in ops:
            readers.setdefault(o, []).append(i)
    term = {}
    for t, g in enumerate(tg):
        term.setdefault(("g", g), []).append(t)
    Tm = [1 << i for i in range(8)]
    Tops = [None] * 8
    adj, contribs = {}, {}
    keys = [("g", i) for i in reversed(range(K))] + [("z", t) for t in range(tau)] + [("u", u) for u in range(8)]
    for key in keys:
        c = list(term.get(key, [])) + [adj[("g", r)] for r in readers.get(key, [])]
        assert c, ("signal never read", key)
        if order == "random":
            rng.shuffle(c)
        elif order == "level":
            c.sort(key=lambda s: -level_pair(Tm[s]))
        contribs[key] = list(c)
        acc = c[0]
        for x in c[1:]:
            Tm.append(Tm[acc] ^ Tm[x])
            Tops.append((acc, x))
            acc = len(Tm) - 1
        adj[key] = acc
    # check adjoints against the definition (set of targets whose formal mask contains the signal)
    for t in range(tau):
        z = Tm[adj[("z", t)]]
        for p in range(8):
            assert ((z >> p) & 1) == ((nm[tg[p]] >> t) & 1)
    for u in range(8):
        a = Tm[adj[("u", u)]]
        for p in range(8):
            assert ((a >> p) & 1) == ((beta[tg[p]] >> u) & 1)
    return dict(K=K, tau=tau, phi=phi, Tm=Tm, Tops=Tops, adj=adj, contribs=contribs, beta=beta, nm=nm)


def A_vec(i):
    return E4(i) | (1 << (4 + (i - 1) % 4)) | (1 << (4 + i))


def B_vec(i):
    return E4(i) << 4


def tstats(M):
    """Quantities of section 3 and checks of Lemma 3.1 (a)-(d); raises AssertionError on a violation."""
    Tm, Tops, K, tau = M["Tm"], M["Tops"], M["K"], M["tau"]
    NT = len(Tm)
    nT = NT - 8
    assert nT == K - tau
    for i in range(4):
        assert Tm[M["adj"][("u", i)]] == A_vec(i), "A_i"
        assert Tm[M["adj"][("u", 4 + i)]] == B_vec(i), "B_i"
    zetas = [Tm[M["adj"][("z", t)]] for t in range(tau)]
    zb = reduce_basis(zetas)
    assert all(inspan(zb, e) for e in (0b0011, 0b0110, 0b1100)), "exports do not span Even(w)+0"
    first = {1 << c: c for c in range(4)}
    cls = [None] * NT
    f_w = Dn = N0 = 0
    entries, texits, nonentry_dup = [], [], []
    for i in range(8, NT):
        a, b = Tops[i]
        om, oa, ob = Tm[i] & 15, Tm[a] & 15, Tm[b] & 15
        if om == 0:
            N0 += 1
            cls[i] = "N0"
            if oa and ob and Tm[i]:
                texits.append(i)
        elif om in first:
            Dn += 1
            cls[i] = "dup"
            if (oa == 0) != (ob == 0):
                pi = a if oa == 0 else b
                entries.append((i, pi))
            else:
                nonentry_dup.append(i)
        else:
            first[om] = i
            f_w += 1
            cls[i] = "first"
            assert oa and ob and oa != ob, "first gate with omega=0 operand or operands in one fibre"
    assert nT == f_w + Dn + N0 and K == f_w + tau + Dn + N0
    # (a) T_w is a circuit on w with masks the omegas, containing E_c(w); projected exports are its signals
    for i in range(8, NT):
        if cls[i] == "first":
            a, b = Tops[i]
            ra, rb = first[Tm[a] & 15], first[Tm[b] & 15]
            assert ra < i and rb < i and ra != rb
            assert (Tm[ra] ^ Tm[rb]) & 15 == Tm[i] & 15
    for c in range(4):
        assert E4(c) in first and first[E4(c)] >= 8
    proj = [z & 15 for z in zetas if z & 15]
    assert all(p in first for p in proj)
    assert reduce_basis(proj) and all(inspan(reduce_basis(proj), e) for e in (3, 6, 12))
    assert f_w + len(proj) >= 10, "r=1 bound on T_w violated"
    assert f_w + tau >= 10, "3.1(a)"
    # (b)
    tau1 = len(entries)
    Pi = reduce_basis([Tm[pi] >> 4 for _, pi in entries])
    for i in range(NT):
        if Tm[i] & 15:
            assert inspan(Pi, Tm[i] >> 4), "3.1(b) span"
    assert Dn >= tau1 >= 3, "3.1(b) counts"
    # (c)
    Bg = {}
    for i in range(8, NT):
        for c in range(4):
            if Tm[i] == B_vec(c):
                Bg.setdefault(c, i)
    assert len(Bg) == 4 and all(cls[g] == "N0" for g in Bg.values()) and N0 >= 4, "3.1(c)"
    # (d)
    if tau1 == 3:
        pis = [pi for _, pi in entries]
        assert len(set(pis)) == 3
        for p in pis:
            assert p >= 8 and Tm[p] & 15 == 0 and Tm[p] and popc(Tm[p] >> 4) % 2 == 0
        assert not set(pis) & set(Bg.values())
        assert N0 >= 7, "3.1(d)"
    # symmetric decomposition by second part
    firsts = {1 << c: 4 + c for c in range(4)}
    N10 = fs = Ds = ent2 = 0
    for i in range(8, NT):
        a, b = Tops[i]
        s, sa, sb = Tm[i] >> 4, Tm[a] >> 4, Tm[b] >> 4
        if s == 0:
            N10 += 1
        elif s in firsts:
            Ds += 1
            if (sa == 0) != (sb == 0):
                ent2 += 1
        else:
            firsts[s] = i
            fs += 1
    assert K == tau + N10 + fs + Ds and fs >= 8 and Ds >= ent2 >= 4
    return dict(K=K, tau=tau, T=nT, f_w=f_w, D=Dn, N_0=N0, tau1=tau1, texits=len(texits),
                nonentry_dup=len(nonentry_dup), N10=N10, fs=fs, Ds=Ds, tau2=ent2)


def fmt(st):
    return "(K, tau, |T|, f_w, D, N_0, tau') = (%d, %d, %d, %d, %d, %d, %d)  T-exits %d  non-entry dups %d  " \
           "[s-decomp: N10 %d f_w' %d D' %d tau'' %d]" % (
               st["K"], st["tau"], st["T"], st["f_w"], st["D"], st["N_0"], st["tau1"], st["texits"],
               st["nonentry_dup"], st["N10"], st["fs"], st["Ds"], st["tau2"])
