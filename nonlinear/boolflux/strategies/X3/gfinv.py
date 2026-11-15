"""X3: inversion tables in GF(2^n) and exact MC by SAT (H4's CHM encoder).
usage: gfinv.py N K [solver]   -> SAT/UNSAT for k ANDs, prints decoded circuit as JSON on SAT."""
import sys, json, time, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'H4'))
POLY = {2: 0b111, 3: 0b1011, 4: 0b10011, 5: 0b100101, 6: 0b1000011, 7: 0b10000011, 8: 0x11B}

def gmul(a, b, n):
    p = POLY[n]; r = 0
    while b:
        if b & 1: r ^= a
        a <<= 1
        if a >> n: a ^= p
        b >>= 1
    return r

def gpow(a, e, n):
    r = 1
    while e:
        if e & 1: r = gmul(r, a, n)
        a = gmul(a, a, n); e >>= 1
    return r

def inv_table(n):
    return [gpow(x, (1 << n) - 2, n) for x in range(1 << n)]

def pow_table(n, e):
    return [gpow(x, e, n) if x else 0 for x in range(1 << n)]

if __name__ == '__main__':
    import chm
    n, k = int(sys.argv[1]), int(sys.argv[2])
    solver = sys.argv[3] if len(sys.argv) > 3 else 'cadical153'
    tab = inv_table(n)
    res, dt, f = chm.solve(tab, n, n, k, solver)
    print(json.dumps({'n': n, 'k': k, 'sat': res is not None, 'sec': round(dt, 2),
                      'vars': f.n, 'clauses': len(f.cl), 'circ': res}))
    if res:
        assert all(chm.evaluate(res, n, p) == tab[p] for p in range(1 << n))
