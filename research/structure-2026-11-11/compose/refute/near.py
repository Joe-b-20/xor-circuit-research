"""Near-side (one supplying sheet) evaluator.  A check of one fixed hand-written object, not a search.

File format:
  label NAME = u0 u1 a2 ...      far vector; u_c = unit c of w^2 (bits 0..3), a_c = unit c of w^3 (bits 4..7),
                                 b_c = unit c of w^4 (bits 8..11)
  name = x + y                   gate; operands are w0..w3, earlier gates, or label names (an operand that is a
                                 label makes the gate an ENTRY with that label)
  export n1 n2 n3                export signals
  exit name = x + y              an exit across cut 1 (x, y level-1 signals with equal omega)
Reports f1, h1, e1, tau, near1, target check (E_i(w^1) | p_i(w^2)), export check, reducedness on the near side,
formal parts, traces zeta_j, every same-fibre pair (possible exits) with formal difference and value.
"""
import sys

def parse_vec(toks):
    v = 0
    for t in toks:
        g = {'u': 0, 'a': 4, 'b': 8}[t[0]]
        v ^= 1 << (g + int(t[1:]))
    return v

def E(c):
    return 15 ^ (1 << c)

def P(c):  # p_c = u_(c-1) + u_c
    return (1 << ((c - 1) % 4)) | (1 << c)

def vs(v):
    if v == 0:
        return '0'
    out = []
    for g, ch in ((0, 'u'), (4, 'a'), (8, 'b')):
        for c in range(4):
            if v >> (g + c) & 1:
                out.append('%s%d' % (ch, c))
    return '+'.join(out)

def rank(vecs):
    basis = []
    for v in vecs:
        for b in basis:
            v = min(v, v ^ b)
        if v:
            basis.append(v)
    return len(basis)

def main(path):
    labels, lname = {}, []
    sig = {}            # name -> (omega, s, formal frozenset of entry indices)
    order = []
    kind = {}
    entries = []        # (gate name, label name)
    exports, exits = [], []
    for c in range(4):
        sig['w%d' % c] = (1 << c, 0, frozenset())
    seen_omega = {1 << c for c in range(4)}
    for line in open(path):
        line = line.split('#')[0].strip()
        if not line:
            continue
        if line.startswith('label '):
            nm, rhs = line[6:].split('=')
            labels[nm.strip()] = parse_vec(rhs.split())
            lname.append(nm.strip())
            continue
        if line.startswith('export '):
            exports = line.split()[1:]
            continue
        isexit = line.startswith('exit ')
        if isexit:
            line = line[5:]
        nm, rhs = [t.strip() for t in line.split('=')]
        a, b = [t.strip() for t in rhs.split('+')]
        if isexit:
            oa, sa, fa = sig[a]; ob, sb, fb = sig[b]
            assert oa == ob and oa != 0, 'exit operands not in one fibre: ' + line
            exits.append((nm, a, b, sa ^ sb, fa ^ fb, len(entries)))
            continue
        if b in labels and a not in labels:
            pass
        elif a in labels:
            a, b = b, a
        if b in labels:
            oa, sa, fa = sig[a]
            j = len(entries)
            entries.append((nm, b))
            sig[nm] = (oa, sa ^ labels[b], fa ^ frozenset([j]))
            kind[nm] = 'entry'
        else:
            oa, sa, fa = sig[a]; ob, sb, fb = sig[b]
            o = oa ^ ob
            assert o != 0, 'level-1 gate with zero omega (an exit?): ' + line
            sig[nm] = (o, sa ^ sb, fa ^ fb)
            if o in seen_omega:
                kind[nm] = 'h'
            else:
                kind[nm] = 'first'
                seen_omega.add(o)
        order.append(nm)
    f1 = sum(1 for n in order if kind[n] == 'first')
    h1 = sum(1 for n in order if kind[n] == 'h')
    e1 = len(entries)
    tau = len(exports)
    print('f1 %d  h1 %d  e1 %d  tau %d  near1 %d' % (f1, h1, e1, tau, f1 + h1 + tau))
    # targets
    vals = {n: (sig[n][0], sig[n][1]) for n in sig}
    tgt = {}
    for i in range(4):
        hit = [n for n in sig if vals[n] == (E(i), P(i))]
        tgt[i] = hit[0] if hit else None
        print('target %d (E_%d | %s): %s' % (i, i, vs(P(i)), hit if hit else 'MISSING'))
    # exports
    ev = []
    ok = True
    for n in exports:
        o, s, f = sig[n]
        if s != 0 or bin(o).count('1') % 2:
            ok = False
        ev.append(o)
    print('exports', exports, 'pure-even' if ok else 'NOT pure even', 'rank', rank(ev))
    # reducedness (near side): distinct nonzero values, labels distinct from level-1 values automatically
    allv = {}
    red = True
    for n in ['w0', 'w1', 'w2', 'w3'] + order:
        key = (sig[n][0], sig[n][1])
        if key in allv:
            print('  REPEATED value', n, allv[key]); red = False
        allv[key] = n
    lv = set(labels[l] for l in lname)
    for nm, a, b, s, f, t in exits:
        if s == 0 or s in lv:
            print('  exit', nm, 'value zero or equal to a label'); red = False
    ex_vals = [x[3] for x in exits]
    if len(set(ex_vals)) != len(ex_vals):
        print('  repeated exit values'); red = False
    print('near-side reduced:', red)
    # formal parts
    print('entries (time order):', ', '.join('%s:%s=%s' % (g, l, vs(labels[l])) for g, l in entries))
    print('label rank', rank([labels[l] for _, l in entries]))
    for n in order:
        o, s, f = sig[n]
        print('  %-5s %-6s omega %s  formal {%s}  s=%s' % (n, kind[n], format(o, '04b')[::-1], ','.join(str(j) for j in sorted(f)), vs(s)))
    # traces
    if all(tgt[i] for i in range(4)):
        for j, (g, l) in enumerate(entries):
            z = ''.join('1' if j in sig[tgt[i]][2] else '0' for i in range(4))
            print('  zeta_%d (%s, label %s) = %s' % (j, g, l, z))
    for nm, a, b, s, f, t in exits:
        print('exit %s = %s + %s: formal {%s} value %s (entries before it: %d)' % (nm, a, b, ','.join(str(j) for j in sorted(f)), vs(s), t))
    # same-fibre pairs
    byo = {}
    for n in ['w0', 'w1', 'w2', 'w3'] + order:
        byo.setdefault(sig[n][0], []).append(n)
    print('same-fibre pairs (possible exits):')
    for o, ns in byo.items():
        for i in range(len(ns)):
            for k in range(i + 1, len(ns)):
                f = sig[ns[i]][2] ^ sig[ns[k]][2]
                print('   %s + %s: formal {%s} value %s' % (ns[i], ns[k], ','.join(str(j) for j in sorted(f)), vs(sig[ns[i]][1] ^ sig[ns[k]][1])))

main(sys.argv[1])
