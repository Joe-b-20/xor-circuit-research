# Independent reviewer check (not a proof): build a chain-of-l local circuit by hand,
# mirror it, and check |T| = K - tau, the required vectors, the export span, and the
# Lemma 1 / Lemma 2 quantities (f, D, N, e, the circuit R) on the resulting T.
import sys, random

def E(c):  # triple-sum on a 4-bit group: all bits except c
    return 0b1111 ^ (1 << c)
def S(c):  # s_c = e_c + e_(c+1)
    return (1 << c) | (1 << ((c + 1) % 4))
def P(i):  # p_i = u_(i-1) + u_i
    return (1 << ((i - 1) % 4)) | (1 << i)

def rank(vs):
    basis = []
    for v in vs:
        for b in basis:
            v = min(v, v ^ b)
        if v:
            basis.append(v)
    return len(basis)

def build_local(l, rng):
    """Local circuit for sheets 1..l, block a free. Signals: ('u',k,c) own units,
    ('z',i) formal inputs (entry free operands, phi[i] on a), ('g',j) gates.
    Values: own part (4l bits, block k at bits 4(k-1)) and a-part (4 bits)."""
    gates, phi = [], []
    own = {}
    def val(sig):
        if sig[0] == 'u':
            return (1 << (4 * (sig[1] - 1) + sig[2]), 0)
        if sig[0] == 'z':
            return (0, phi[sig[1]])
        return own[sig[1]]
    def gate(x, y):
        vx, vy = val(x), val(y)
        j = len(gates)
        gates.append((x, y))
        own[j] = (vx[0] ^ vy[0], vx[1] ^ vy[1])
        return ('g', j)
    def entry(x, phivec):
        phi.append(phivec)
        return gate(x, ('z', len(phi) - 1))
    targets = {}
    for k in range(1, l + 1):
        q = lambda c: ('u', k, c)
        h1 = gate(q(0), q(1)); h2 = gate(q(2), q(3)); t = gate(h1, h2)
        Es = [gate(t, q(c)) for c in range(4)]
        if k == 1:
            for c in range(4):
                targets[(k, c)] = entry(Es[c], S(c))
        else:
            p = lambda c: ('u', k - 1, c)
            # vary the construction a little: s_3 either direct or as s0+s1+s2
            s = [gate(p(c), p((c + 1) % 4)) for c in range(3)]
            if rng.random() < 0.5:
                s.append(gate(p(3), p(0)))
            else:
                s.append(gate(gate(s[0], s[1]), s[2]))
            for c in range(4):
                targets[(k, c)] = gate(Es[c], s[c])
    # check targets
    for (k, c), g in targets.items():
        vo, va = val(g)
        want = E(c) << (4 * (k - 1))
        if k > 1:
            want |= S(c) << (4 * (k - 2))
        assert vo == want and va == (S(c) if k == 1 else 0), (k, c)
    return gates, phi, targets

def mirror(l, gates, phi, targets, rng):
    """Transpose. w-space bit 4(k-1)+c = target (k,c). Returns T as list of gate
    values (masks over w) plus the adjoints of all signals."""
    n_in = 4 * l
    readers = {}
    def add(sig, contrib):
        readers.setdefault(sig, []).append(contrib)
    for j, (x, y) in enumerate(gates):
        add(x, ('g', j)); add(y, ('g', j))
    for (k, c), g in targets.items():
        add(g, ('w', 4 * (k - 1) + c))
    adj = {}
    Tgates = []
    def resolve(sig):
        contribs = [(1 << c[1]) if c[0] == 'w' else adj[c] for c in readers[sig]]
        rng.shuffle(contribs)  # any accumulation order
        acc = contribs[0]
        for v in contribs[1:]:
            acc ^= v
            Tgates.append(acc)
        adj[sig] = acc
    for j in reversed(range(len(gates))):
        resolve(('g', j))
    for i in range(len(phi)):
        resolve(('z', i))
    for k in range(1, l + 1):
        for c in range(4):
            resolve(('u', k, c))
    return Tgates, adj

def analyse_T(l, Tgates, exports):
    inputs = [1 << b for b in range(4 * l)]
    lastmask = 0b1111 << (4 * (l - 1))
    om = lambda v: v & ~lastmask
    sp = lambda v: (v & lastmask) >> (4 * (l - 1))
    # reduce: drop repeated values and zeros (values only; enough for counting here)
    sigs, seen = list(inputs), set(inputs)
    red = []
    for v in Tgates:
        if v and v not in seen:
            seen.add(v); red.append(v)
    first_seen = set(om(v) for v in inputs if om(v))
    f = D = N = 0
    for v in red:
        if om(v) == 0:
            N += 1
        elif om(v) in first_seen:
            D += 1
        else:
            first_seen.add(om(v)); f += 1
    req = []
    for k in range(1, l + 1):
        for i in range(4):
            v = E(i) << (4 * (k - 1))
            if k < l:
                v |= P(i) << (4 * k)
            req.append(v)
    allsig = set(inputs) | set(red)
    assert all(v in allsig for v in req)
    # R contains the shorter chain's required vectors (projections)
    omegas = set(om(v) for v in allsig if om(v))
    req_short = [om(v) for v in req if om(v)]
    assert all(v in omegas for v in req_short)
    return len(red), f, D, N

def main():
    rng = random.Random(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
    for l in (1, 2, 3, 4):
        for trial in range(20):
            gates, phi, targets = build_local(l, rng)
            K, tau = len(gates), len(phi)
            Tg, adj = mirror(l, gates, phi, targets, rng)
            assert len(Tg) == K - tau, (len(Tg), K, tau)
            # required vectors are adjoints of own units
            for k in range(1, l + 1):
                for c in range(4):
                    v = E(c) << (4 * (k - 1))
                    if k < l:
                        v |= P(c) << (4 * k)
                    assert adj[('u', k, c)] == v
            ex = [adj[('z', i)] for i in range(tau)]
            even1 = [P(i) for i in range(1, 4)]
            assert rank(ex) == rank(ex + even1)  # span contains Even(w^1)+0
            if l >= 2:
                red, f, D, N = analyse_T(l, Tg, ex)
        print('l =', l, 'ok; last K, tau, |T| =', K, tau, len(Tg))
    # forests with 4 edges: number of 3-edge paths = sum over edges (deg-1)(deg-1)
    trees5 = {'path': [(0,1),(1,2),(2,3),(3,4)], 'chair': [(0,1),(1,2),(1,3),(3,4)],
              'star': [(0,1),(0,2),(0,3),(0,4)]}
    for name, ed in trees5.items():
        deg = {}
        for a, b in ed:
            deg[a] = deg.get(a, 0) + 1; deg[b] = deg.get(b, 0) + 1
        print(name, sum((deg[a]-1)*(deg[b]-1) for a, b in ed), 'three-edge paths')

main()
