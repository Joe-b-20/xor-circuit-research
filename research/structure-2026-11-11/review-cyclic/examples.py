"""Independent reviewer checks of Examples 1-4 of cyclic/REPORT.md (own code)."""
import itertools, subprocess, random, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))

def vec(s):  # string of coefficients of e1..en -> int, bit i = coefficient of e_(i+1)
    return sum(1 << i for i, ch in enumerate(s) if ch == '1')

def vstr(v, n):
    return ''.join('1' if (v >> i) & 1 else '0' for i in range(n))

def rank_f2(rows):
    basis = {}
    r = 0
    for v in rows:
        while v:
            h = v.bit_length() - 1
            if h in basis:
                v ^= basis[h]
            else:
                basis[h] = v; r += 1; break
    return r

def triples(S):
    S = sorted(S); Sset = set(S); out = []
    for i, a in enumerate(S):
        for b in S[i + 1:]:
            c = a ^ b
            if c in Sset and c > b:
                out.append((a, b, c))
    return out

def is_cyclic(S, n):
    S = sorted(S); ix = {v: i for i, v in enumerate(S)}
    rows = [sum(1 << ix[p] for p in t) for t in triples(S)]
    return rank_f2(rows) == len(S) - n

def closure(S, n):
    have = {1 << i for i in range(n)}
    S = set(S)
    ch = True
    while ch:
        ch = False
        for v in S - have:
            if any((v ^ a) in have for a in have):
                have.add(v); ch = True
    return have

def lmin(n, targets, maxk, printk=-1):
    exe = os.path.join(HERE, 'lmin')
    out = subprocess.run([exe, str(n), str(maxk), str(printk)] + [str(t) for t in targets],
                         capture_output=True, text=True, check=True).stdout
    return out

def matmul(A, B, n):  # rows as ints; (A*B) row i = sum_j A[i][j] B row j
    return [ (lambda r: r)(sum_rows([B[j] for j in range(n) if (A[i] >> j) & 1])) for i in range(n)]

def sum_rows(rs):
    x = 0
    for r in rs: x ^= r
    return x

def transpose(A, n):
    return [sum(((A[i] >> j) & 1) << i for i in range(n)) for j in range(n)]

def summary(out):
    res = {}
    for line in out.splitlines():
        if line.startswith('k='):
            d = dict(kv.split('=') for kv in line.split())
            res[int(d['k'])] = (int(d['cyclic']), int(d['circuit']), int(d['circuit_not_cyclic']), int(d['size']))
    return res

def report_L(name, n, rows, maxk):
    out = lmin(n, rows, maxk)
    res = summary(out)
    lc = next((res[k][3] for k in sorted(res) if res[k][0] > 0), None)
    l = next((res[k][3] for k in sorted(res) if res[k][1] > 0), None)
    print(f"{name}: per k (cyclic, circuit, bad, size): {res}")
    print(f"{name}: L_cyc = {lc}, L = {l}  (None = > searched range)")
    return lc, l

def example1():
    print("== Example 1 ==")
    n = 5
    q1, a, b, c, q2, q3 = map(vec, ['11100', '11110', '11111', '01111', '00111', '11011'])
    E = [1 << i for i in range(n)]
    Q = [q1, a, b, c, q2, q3]
    S = set(E + Q)
    T = triples(S)
    names = {q1: 'q1', a: 'a', b: 'b', c: 'c', q2: 'q2', q3: 'q3'}
    for i in range(n): names[1 << i] = f'e{i+1}'
    print("triples:", sorted([sorted(names[p] for p in t) for t in T]))
    claimed = [{'e4', 'q1', 'a'}, {'e5', 'a', 'b'}, {'e1', 'b', 'c'}, {'e2', 'c', 'q2'}, {'e3', 'b', 'q3'}, {'q1', 'q2', 'q3'}]
    got = [set(names[p] for p in t) for t in T]
    print("triples match claim:", sorted(map(sorted, got)) == sorted(map(sorted, claimed)))
    print("cyclic:", is_cyclic(S, n), " closure of E =", sorted(names[v] for v in closure(S, n)))
    report_L("Ex1 M=Q", n, Q, 3)
    Qb = [v for v in Q if v != b]
    report_L("Ex1 M=Q-b", n, Qb, 3)
    # all non-circuit cyclic sets of size 6 at n = 5, and the coordinate-permutation orbit of S
    nonunit = [v for v in range(1, 32) if bin(v).count('1') >= 2]
    found = []
    for X in itertools.combinations(nonunit, 6):
        SS = set(E) | set(X)
        if is_cyclic(SS, n) and len(closure(SS, n)) < len(SS):
            found.append(frozenset(X))
    def perm(v, p):
        return sum(((v >> i) & 1) << p[i] for i in range(n))
    orbit = set(frozenset(perm(v, p) for v in Q) for p in itertools.permutations(range(n)))
    print("n=5 non-circuit cyclic sets of size 6:", len(found), " orbit of Ex1 under S_5:", len(orbit),
          " equal:", set(found) == orbit)
    # Theorem B at n = 5: no non-circuit cyclic set of size <= 5
    small = 0
    for k in range(1, 6):
        for X in itertools.combinations(nonunit, k):
            SS = set(E) | set(X)
            if is_cyclic(SS, n) and len(closure(SS, n)) < len(SS):
                small += 1
    print("n=5 non-circuit cyclic sets of size <= 5:", small)
    # Theorem B at n = 4
    E4 = [1 << i for i in range(4)]
    nonunit4 = [v for v in range(1, 16) if bin(v).count('1') >= 2]
    bad4 = 0
    for k in range(1, len(nonunit4) + 1):
        for X in itertools.combinations(nonunit4, k):
            SS = set(E4) | set(X)
            if is_cyclic(SS, 4) and len(closure(SS, 4)) < len(SS):
                bad4 += 1
    print("n=4 non-circuit cyclic sets (all sizes):", bad4)
    return S, T

def example2():
    print("== Example 2 ==")
    n = 6
    def lin(*xs):
        return sum(1 << (x - 1) for x in xs)
    B = [lin(2, 6), lin(3, 4), lin(1, 4, 5), lin(5, 6), lin(1, 3), lin(1, 2, 5)]
    A = [vec(s) for s in ['100101', '111110', '100111', '110111', '011010', '011110']]
    I = [1 << i for i in range(n)]
    print("A*B = I:", matmul(A, B, n) == I, " B*A = I:", matmul(B, A, n) == I)
    # 7-gate circuit for B: t = x1+x5; y3 = t+x4; y6 = t+x2 plus 5 single gates
    circ = set(I) | {lin(1, 5)} | set(B)
    print("claimed circuit mask set size - n:", len(circ) - n, " is circuit set:", len(closure(circ, n)) == len(circ))
    lcA, lA = report_L("Ex2 A", n, A, 3)
    lcB, lB = report_L("Ex2 B", n, B, 2)
    # the seven equations read from the outputs: unknowns x1..x6, t; known y's
    # equations: y1=x2+x6, y2=x3+x4, y4=x5+x6, y5=x1+x3, t=x1+x5, y3=t+x4, y6=t+x2
    eqs = [{'x2', 'x6'}, {'x3', 'x4'}, {'x5', 'x6'}, {'x1', 'x3'}, {'x1', 'x5', 't'}, {'t', 'x4'}, {'t', 'x2'}]
    unk = ['x1', 'x2', 'x3', 'x4', 'x5', 'x6', 't']
    print("min unknowns per equation:", min(len(e) for e in eqs),
          " min occurrences per unknown:", min(sum(u in e for e in eqs) for u in unk))
    M = [sum(1 << unk.index(u) for u in e) for e in eqs]
    print("7x7 unknown matrix rank:", rank_f2(M))

def example3():
    print("== Example 3 ==")
    n = 7
    B = [vec(s) for s in ['0101010', '1110000', '1010001', '0110001', '1011000', '0001110', '0010011']]
    A = [vec(s) for s in ['1110101', '1101101', '0111000', '1001001', '0101111', '1100100', '1011101']]
    I = [1 << i for i in range(n)]
    print("A*B = I:", matmul(A, B, n) == I, " B*A = I:", matmul(B, A, n) == I)
    print("row weights A:", [bin(r).count('1') for r in A], " col weights A:", [bin(r).count('1') for r in transpose(A, n)])
    bnd = I + A
    minrel = None
    for w in range(1, 8):
        for X in itertools.combinations(range(14), w):
            if sum_rows([bnd[i] for i in X]) == 0:
                minrel = w; break
        if minrel: break
    print("min relation weight among 14 boundary vectors:", minrel)
    report_L("Ex3 A", n, A, 4)
    report_L("Ex3 B", n, B, 3)
    report_L("Ex3 A^T", n, transpose(A, n), 3)
    return A

def example4():
    print("== Example 4 ==")
    V = [f'a{i}' for i in range(4)] + [f'r{i}' for i in range(12)] + ['o']
    vi = {v: i for i, v in enumerate(V)}
    tris = []
    for i in range(12):
        tris.append((f'a{i % 4}', f'a{(i + 1) % 4}', f'r{i}'))
        tris.append((f'a{(i + 1) % 4}', f'r{i}', f'r{(i + 1) % 12}'))
        tris.append((f'r{i}', f'r{(i + 1) % 12}', 'o'))
    edges = set()
    for t in tris:
        for u, w in itertools.combinations(t, 2):
            edges.add(frozenset((u, w)))
    edges = sorted(edges, key=lambda e: sorted(e))
    print("vertices", len(V), "edges", len(edges), "listed triangles", len(set(frozenset(t) for t in tris)))
    ev = {e: sum(1 << vi[x] for x in e) for e in edges}
    S = set(ev.values())
    print("edge vectors distinct:", len(S) == len(edges), " span dim:", rank_f2(list(S)))
    T = triples(S)
    trisets = set(frozenset(ev[frozenset(p)] for p in itertools.combinations(t, 2)) for t in tris)
    print("triples of S:", len(T), " equal to the triangles:", set(frozenset(t) for t in T) == trisets)
    eidx = {e: k for k, e in enumerate(edges)}
    # F2 rank of triangles as vectors over edges
    rows2 = [sum(1 << eidx[frozenset(p)] for p in itertools.combinations(t, 2)) for t in tris]
    print("F2 rank of triangles:", rank_f2(rows2), " (52-16 =", 52 - 16, ")")
    # F3 rank of oriented boundary: orient edge u<v by vertex index; boundary of (x<y<z) = [yz] - [xz] + [xy]
    def rank_mod(rows, p):
        rows = [r[:] for r in rows]; r = 0; ncol = len(rows[0])
        for c in range(ncol):
            piv = next((i for i in range(r, len(rows)) if rows[i][c] % p), None)
            if piv is None: continue
            rows[r], rows[piv] = rows[piv], rows[r]
            inv = pow(rows[r][c], p - 2, p)
            rows[r] = [(x * inv) % p for x in rows[r]]
            for i in range(len(rows)):
                if i != r and rows[i][c] % p:
                    f = rows[i][c]
                    rows[i] = [(x - f * y) % p for x, y in zip(rows[i], rows[r])]
            r += 1
        return r
    rows3 = []
    for t in tris:
        x, y, z = sorted(t, key=lambda v: vi[v])
        row = [0] * len(edges)
        row[eidx[frozenset((y, z))]] += 1
        row[eidx[frozenset((x, z))]] -= 1
        row[eidx[frozenset((x, y))]] += 1
        rows3.append(row)
    print("F3 rank of oriented triangles:", rank_mod(rows3, 3), " Q-like check mod 5:", rank_mod(rows3, 5))
    # random spanning trees: closure of tree inside S never reaches S
    rng = random.Random(1)
    evl = list(ev.values())
    worst = 0
    for trial in range(2000):
        order = evl[:]; rng.shuffle(order)
        tree = []
        for v in order:
            if rank_f2(tree + [v]) > len(tree): tree.append(v)
            if len(tree) == 16: break
        have = set(tree); ch = True
        while ch:
            ch = False
            for v in S - have:
                if any((v ^ a) in have for a in have):
                    have.add(v); ch = True
        worst = max(worst, len(have))
    print("2000 random spanning trees: largest closure", worst, "of", len(S))

if __name__ == '__main__':
    which = sys.argv[1:] or ['1', '2', '3', '4']
    if '1' in which: example1()
    if '2' in which: example2()
    if '3' in which: example3()
    if '4' in which: example4()
