#!/usr/bin/env python3
"""One-AND 'packing' of a bilinear 18-product bottom into 17 products (the mechanism behind NIST's 117).

Bilinear decomposition D = sum_k u_k (x) v_k (x) w_k (u: Y-form, v: X-form, w: output mask), front F with
level-1 ANDs A*B.  For a level-1 product with operand plane pi = span(A, B) and two pieces
s (x) A' (x) w and t (x) B' (x) w of D with the same w, s != t and {A', B'} two of the three nonzero forms
of pi, the single AND
        P = (A' + t)(B' + s) = A'B' + s.A' + t.B' + s.t
gives both pieces; A'B' = AB (+ a linear form) is cancelled by XORing the existing level-1 AND into the
outputs of w; the Y*Y part s.t is cancelled by adding Y-forms nu_k to the X-operand of other terms
(u_k (v_k + nu_k) adds u_k nu_k, no bilinear change): a GF(2) linear system on the cross monomials
y_i y_j (i < j) per output, solved for the fewest modified terms (subsets up to --kmax).  Diagonal
parts (y_i^2 = y_i) become linear terms.  Pieces come from the GL(2) re-bases of the term pairs that
share a Y-form (3 configurations per pair).  Every candidate is built (build.py) and checked on 256 inputs.

    pack.py REF FRONT [--kmax 4] [--nb 3] [--out DIR] [--save 20]
"""
import itertools, json, random, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import bottom as BT, flip as FL, qflip as QF, build as BD  # noqa
from boolflux import core  # noqa


def X(v): return v << 1            # x-mask (8 bits) -> 13-bit form
def Y(u): return u << 9            # y-mask (4 bits) -> 13-bit form


def cross(u, nu):
    """cross monomials y_i y_j (i<j) of (u.Y)(nu.Y) as a 6-bit mask, and the diagonal (linear) part."""
    bits = 0; k = 0; diag = 0
    for i in range(4):
        for j in range(i + 1, 4):
            if ((u >> i & 1) and (nu >> j & 1)) ^ ((u >> j & 1) and (nu >> i & 1)): bits |= 1 << k
            k += 1
        if u >> i & 1 and nu >> i & 1: diag |= 1 << i
    return bits, diag


def solve_cancel(target, terms, kmax):
    """target[o] = 6-bit cross mask to cancel on output o.  terms: list of (u, w) eligible (index aligned).
    Find a smallest set K of term indices and nu_k != 0 with sum_k [o in w_k] cross(u_k, nu_k) = target[o]."""
    if all(t == 0 for t in target): return []
    n = len(terms)
    tvec = 0
    for o in range(8): tvec |= target[o] << (6 * o)
    for size in range(1, kmax + 1):
        for K in itertools.combinations(range(n), size):
            # unknowns: nu_k (4 bits each); columns = effect of each unknown bit
            cols = []
            for k in K:
                u, w = terms[k]
                for b in range(4):
                    cb, _ = cross(u, 1 << b)
                    v = 0
                    for o in range(8):
                        if w >> o & 1: v |= cb << (6 * o)
                    cols.append(v)
            # solve cols * x = tvec over GF(2) (48 x 4|K|)
            rows = []   # (pivot, vec, combo)
            for idx, cv in enumerate(cols):
                combo = 1 << idx
                for piv, r, cbm in rows:
                    if cv >> piv & 1: cv ^= r; combo ^= cbm
                if cv:
                    piv = cv.bit_length() - 1
                    rows = [(p2, r2 ^ cv if r2 >> piv & 1 else r2, c2 ^ combo if r2 >> piv & 1 else c2) for p2, r2, c2 in rows]
                    rows.append((piv, cv, combo))
            t = tvec; sol = 0
            for piv, r, cbm in rows:
                if t >> piv & 1: t ^= r; sol ^= cbm
            if t: continue
            nus = []
            ok = True
            for q, k in enumerate(K):
                nu = (sol >> (4 * q)) & 0xF
                if nu == 0: ok = False; break
                nus.append((k, nu))
            if ok: return nus
    return None


def main():
    a = sys.argv[1:]
    ref, front = a[0], a[1]
    kmax = int(a[a.index('--kmax') + 1]) if '--kmax' in a else 4
    nb = int(a[a.index('--nb') + 1]) if '--nb' in a else 3
    out = Path(a[a.index('--out') + 1]) if '--out' in a else Path('pack'); out.mkdir(parents=True, exist_ok=True)
    nsave = int(a[a.index('--save') + 1]) if '--save' in a else 20
    rc, Yt = FL.ref_basis(ref)
    fc = BT.load(front)
    ext = FL.extract(fc, Yt)
    assert ext is not None, 'FRONT bottom is not bilinear'
    D, ten, const = ext
    free0, fixed0, lin0 = QF.decompose(fc, Yt)
    # level-1 products: planes
    planes = []
    for k, (L, R, w) in enumerate(fixed0):
        if (L >> 9) or (R >> 9): continue
        A_, B_ = (L >> 1) & 0xFF, (R >> 1) & 0xFF
        planes.append((k, A_, B_, L & 1, R & 1))
    # baseline build
    def build_cost(free, fixed, lin):
        best = None
        for s in range(nb):
            c = BD.build(fc, Yt, free, fixed, lin, random.Random(s))
            m = c.metrics(BD.MODEL)
            if best is None or (m['G'], m['GD']) < best[0]: best = ((m['G'], m['GD']), c)
        return best
    base = build_cost(free0, fixed0, lin0)
    print('base rank', len(free0), 'built', base[0], flush=True)
    # term pairs sharing u
    byu = {}
    for idx, (u, v, w) in enumerate(D): byu.setdefault(u, []).append(idx)
    pairs = [(u, ix) for u, ix in byu.items() if len(ix) == 2]
    def configs(ix):
        (u, v1, w1), (u_, v2, w2) = D[ix[0]], D[ix[1]]
        return [[(v1, w1), (v2, w2)], [(v1 ^ v2, w1), (v2, w1 ^ w2)], [(v1, w1 ^ w2), (v1 ^ v2, w2)]]
    t0 = time.time(); results = []; seen = set()
    log = open(out / 'pack.jsonl', 'a')
    for (u1, ix1), (u2, ix2) in itertools.permutations(pairs, 2):
        for c1i, c1 in enumerate(configs(ix1)):
            for c2i, c2 in enumerate(configs(ix2)):
                for p1 in range(2):
                    for p2 in range(2):
                        vA, w = c1[p1]; vB, w2 = c2[p2]
                        if w != w2 or vA == vB: continue
                        for (fk, A_, B_, ca, cb) in planes:
                            pi = {A_, B_, A_ ^ B_}
                            if vA not in pi or vB not in pi: continue
                            # P = (vA + u2)(vB + u1): pieces u1 (x) vA + u2 (x) vB on w
                            key = (u1, c1i, p1, u2, c2i, p2, fk)
                            # new term list: other piece of each pair stays
                            rest = [t for i, t in enumerate(D) if i not in ix1 and i not in ix2]
                            rest.append((u1,) + c1[1 - p1]); rest.append((u2,) + c2[1 - p2])
                            free = [(Y(u), X(v), ww) for (u, v, ww) in rest]
                            P = (X(vA) | Y(u2), X(vB) | Y(u1), w)
                            # cancel YY cross of P on w with modifications nu on rest terms' x-operand
                            cp, dp = cross(u2, u1)
                            target = [cp if w >> o & 1 else 0 for o in range(8)]
                            sol = solve_cancel(target, [(u, ww) for (u, v, ww) in rest], kmax)
                            if sol is None:
                                log.write(json.dumps({'key': key, 'cancel': None}) + '\n'); continue
                            free2 = list(free)
                            for k, nu in sol:
                                L, R, ww = free2[k]; free2[k] = (L, R ^ Y(nu), ww)
                            free2.append(P)
                            # fix everything else exactly: corrections and linear terms from the residual
                            fixed = [tuple(t) for t in fixed0]
                            lin = list(lin0)
                            st = QF.State(free2, fixed, lin)
                            goal = QF.total(free0, fixed0, lin0)
                            cur = QF.total(free2, fixed, [0] * 8)
                            ok = True
                            for o in range(8):
                                rows_g, lg = goal[o]; rows_c, lc = cur[o]
                                diffq = [x ^ y for x, y in zip(rows_g, rows_c)]
                                # residual quadratic must be the level-1 product's X*X part (and nothing else)
                                if any(diffq):
                                    qf, lf = QF.prodfun(*fixed0[fk][:2])
                                    if list(qf) == diffq:
                                        L_, R_, w_ = fixed[fk]; fixed[fk] = (L_, R_, w_ ^ (1 << o))
                                        lc ^= lf
                                    else:
                                        ok = False; break
                                lin[o] = lg ^ lc
                            if not ok:
                                log.write(json.dumps({'key': key, 'cancel': 'residual'}) + '\n'); continue
                            assert QF.total(free2, fixed, lin) == goal
                            sig = tuple(sorted(free2)), tuple(fixed), tuple(lin)
                            if sig in seen: continue
                            seen.add(sig)
                            (G, GD), c = build_cost(free2, fixed, lin)
                            assert c.value_table() == BD.AES
                            rec = {'key': key, 'K': len(sol), 'G': G, 'GD': GD, 'A': c.metrics(BD.MODEL)['A'],
                                   'free': free2, 'fixed': fixed, 'lin': lin}
                            log.write(json.dumps(rec) + '\n'); log.flush()
                            results.append((G, GD, len(results), c, rec))
    results.sort(key=lambda t: t[:2])
    print('candidates', len(results), '%.0fs' % (time.time() - t0))
    for G, GD, i, c, rec in results[:nsave]:
        nm = 'pack-g%d-gd%d-%d.circ.txt' % (G, GD, i)
        (out / nm).write_text(core.write_ncff(c, BD.MODEL, comments=['P3 pack.py key %s K %d' % (rec['key'], rec['K'])]))
        print(nm, rec['key'], 'K', rec['K'], 'A', rec['A'])


if __name__ == '__main__':
    main()
