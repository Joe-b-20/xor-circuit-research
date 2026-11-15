#!/usr/bin/env python3
"""Flip-graph search (Kauers-Moosbauer style) on bilinear decompositions of the bottom tensor T.

Representation: a term is (u, v, w): u in GF(2)^4 (Y-form, bitmask), v in GF(2)^8 (X-form over the input
bits), w in GF(2)^8 (the outputs it feeds).  T = sum u (x) v (x) w (Y coordinates of the reference circuit
REF; the Y space x -> L(x^-17) is the same function space in every BP-family circuit, checked on load).

    flip.py extract REF FILE...           print each circuit's bottom as a decomposition (bilinear only)
    flip.py walk REF START_FILE --steps N --seed S --target R --out DIR [--plus-every K]
"""
import json, random, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import bottom as BT  # noqa


def ref_basis(ref):
    c = BT.load(ref)
    T, la, lg, last, Ysig, B = BT.analyse(c)
    Yt = [T[s] for s in Ysig]
    return c, Yt


def basis_for(Yt, n=8):
    from boolflux import core  # noqa
    B = BT.Basis(); B.add(BT.ONES, '1')
    xs = core.input_tables(n)
    for i in range(n): B.add(xs[i], 'x%d' % i)
    for i, t in enumerate(Yt): assert B.add(t, 'y%d' % i)
    return B


def split(cb):
    """coords bitmask over (1, x0..x7, y0..y3) -> (const, xmask, ymask)"""
    return cb & 1, (cb >> 1) & 0xFF, (cb >> 9) & 0xF


def target_tensor(c, Yt):
    """T as dict: (o) -> set of (i, j) with y_i x_j; also constants."""
    T = c.tables()
    mons = BT.monomials(Yt, [T[i] for i in range(c.n)])
    MB = BT.Basis()
    for nm, t in mons: assert MB.add(t, nm)
    ten = [[0] * 4 for _ in range(8)]   # ten[o][i] = 8-bit mask of x_j
    const = 0
    for o, s in enumerate(c.outputs):
        cb = MB.coords(T[s])
        for k in range(len(MB.names)):
            if cb >> k & 1:
                nm = MB.names[k]
                if nm == '1': const |= 1 << o
                elif nm[0] == 'y' and nm[2] == 'x': ten[o][int(nm[1])] ^= 1 << int(nm[3])
                else: raise ValueError('non-bilinear output term ' + nm)
    return ten, const


def tensor_of(terms):
    ten = [[0] * 4 for _ in range(8)]
    for u, v, w in terms:
        for o in range(8):
            if w >> o & 1:
                for i in range(4):
                    if u >> i & 1: ten[o][i] ^= v
    return ten


def extract(c, Yt):
    """Bilinear decomposition of c's bottom in the Y basis Yt, or None if an operand is mixed."""
    T = c.tables()
    B = basis_for(Yt, c.n)
    la, lg = BT.and_levels(c)
    AD = max(la[s] for s in c.outputs)
    last = [j for j, (op, a, b) in enumerate(c.gates) if op in BT.NL and la[c.n + j] == AD]
    prods = []
    for j in last:
        op, a, b = c.gates[j]
        fa = B.coords(T[a]); fb = B.coords(T[b])
        if fa is None or fb is None: return None
        ca, xa, ya = split(fa); cb_, xb, yb = split(fb)
        if ya and not xa and not ca and xb and not yb and not cb_: prods.append((ya, xb, c.n + j))
        elif yb and not xb and not cb_ and xa and not ya and not ca: prods.append((yb, xa, c.n + j))
        else: return None
    # outputs as combinations of products: solve over truth tables
    PB = BT.Basis()
    for k, (u, v, s) in enumerate(prods): assert PB.add(T[s], 'p%d' % k)
    ten, const = target_tensor(c, Yt)
    # bilinear part of output o = output minus constant
    terms = []
    W = [0] * len(prods)
    for o, s in enumerate(c.outputs):
        t = T[s] ^ (BT.ONES if const >> o & 1 else 0)
        cb = PB.coords(t)
        if cb is None: return None
        for k in range(len(prods)):
            if cb >> k & 1: W[k] |= 1 << o
    terms = [(u, v, W[k]) for k, (u, v, s) in enumerate(prods)]
    assert tensor_of(terms) == ten
    return terms, ten, const


def canon(terms):
    return tuple(sorted(terms))


def reduce_terms(terms):
    """Remove zero terms; merge terms sharing two factors."""
    changed = True
    terms = [t for t in terms if t[0] and t[1] and t[2]]
    while changed:
        changed = False
        n = len(terms)
        for i in range(n):
            for j in range(i + 1, n):
                (u1, v1, w1), (u2, v2, w2) = terms[i], terms[j]
                new = None
                if u1 == u2 and v1 == v2: new = (u1, v1, w1 ^ w2)
                elif u1 == u2 and w1 == w2: new = (u1, v1 ^ v2, w1)
                elif v1 == v2 and w1 == w2: new = (u1 ^ u2, v1, w1)
                if new is not None:
                    terms = [t for k, t in enumerate(terms) if k not in (i, j)]
                    if new[0] and new[1] and new[2]: terms.append(new)
                    changed = True
                    break
            if changed: break
    return terms


def flips(terms):
    """All (i, j, axis) with terms i, j equal on axis."""
    out = []
    n = len(terms)
    for i in range(n):
        for j in range(n):
            if i == j: continue
            for ax in range(3):
                if terms[i][ax] == terms[j][ax]: out.append((i, j, ax))
    return out


def do_flip(terms, i, j, ax):
    """terms i, j share factor ax.  a(x)b_i(x)c_i + a(x)b_j(x)c_j = a(x)(b_i+b_j)(x)c_i + a(x)b_j(x)(c_j+c_i)."""
    t = list(terms)
    ti = list(t[i]); tj = list(t[j])
    o1, o2 = [k for k in range(3) if k != ax]
    ti[o1] ^= tj[o1]
    tj[o2] ^= ti[o2]
    t[i] = tuple(ti); t[j] = tuple(tj)
    return t


def plus(terms, rng):
    """Plus transition: a(x)b(x)c -> a(x)b'(x)c + a(x)(b+b')(x)c with random b' (rank + 1), on a random axis."""
    t = list(terms)
    i = rng.randrange(len(t)); ax = rng.randrange(3)
    width = (4, 8, 8)[ax]
    r = rng.randrange(1, 1 << width)
    a = list(t[i]); b = list(t[i])
    if r == a[ax]: return t
    a[ax] = r; b[ax] ^= r
    t[i] = tuple(a); t.append(tuple(b))
    return t


def walk(ten, start, steps, rng, target, maxrank, log, found, plus_every=0):
    terms = reduce_terms(list(start))
    best = len(terms)
    t0 = time.time()
    since = 0
    for st in range(steps):
        F = flips(terms)
        if not F or (plus_every and since > plus_every and len(terms) < maxrank):
            terms = plus(terms, rng); since = 0
            continue
        i, j, ax = rng.choice(F)
        new = reduce_terms(do_flip(terms, i, j, ax))
        terms = new
        since += 1
        r = len(terms)
        if r <= target:
            key = canon(terms)
            if key not in found:
                assert tensor_of(terms) == ten
                found[key] = st
                log.write(json.dumps({'step': st, 't': round(time.time() - t0, 1), 'rank': r, 'terms': key}) + '\n'); log.flush()
        if r < best:
            best = r
            print('step %d rank %d (%.1fs)' % (st, r, time.time() - t0), flush=True)
            since = 0
    return terms, best


def main():
    a = sys.argv[1:]
    cmd, ref = a[0], a[1]
    rc, Yt = ref_basis(ref)
    if cmd == 'extract':
        for f in a[2:]:
            c = BT.load(f)
            r = extract(c, Yt)
            if r is None:
                print(f, 'not bilinear'); continue
            terms, ten, const = r
            print(f, 'rank', len(terms), 'const', bin(const))
            for t in sorted(terms): print('  u=%s v=%s w=%s' % (format(t[0], '04b'), format(t[1], '08b'), format(t[2], '08b')))
    elif cmd == 'walk':
        f = a[2]
        steps = int(a[a.index('--steps') + 1]); seed = int(a[a.index('--seed') + 1])
        target = int(a[a.index('--target') + 1]); out = Path(a[a.index('--out') + 1]); out.mkdir(parents=True, exist_ok=True)
        pe = int(a[a.index('--plus-every') + 1]) if '--plus-every' in a else 0
        maxrank = int(a[a.index('--maxrank') + 1]) if '--maxrank' in a else 20
        c = BT.load(f)
        terms, ten, const = extract(c, Yt)
        rten, rconst = target_tensor(rc, Yt)
        assert ten == rten and const == rconst, 'tensor differs from REF'
        rng = random.Random(seed)
        found = {}
        log = open(out / ('walk-s%d.jsonl' % seed), 'a')
        terms, best = walk(ten, terms, steps, rng, target, maxrank, log, found, pe)
        print('end best rank', best, 'found', len(found))


if __name__ == '__main__':
    main()
