"""P4: small self-contained NCFF reader, simulator and symbolic (atom) decomposition.

Atoms: the 8 inputs x0..x7 and every AND output.  Every XOR/XNOR/NOT signal is an XOR of atoms plus
a constant (symbolic form = (frozenset of atom names, const)).
"""
import re

def _aes_sbox():
    def mul(a, b):
        r = 0
        while b:
            if b & 1: r ^= a
            b >>= 1; a <<= 1
            if a >> 8: a ^= 0x11B
        return r
    inv = [0] * 256
    for a in range(1, 256):
        for b in range(1, 256):
            if mul(a, b) == 1: inv[a] = b; break
    out = []
    for x in range(256):
        b = inv[x]; v = 0
        for i in range(8):
            v |= (((b >> i) ^ (b >> ((i + 4) % 8)) ^ (b >> ((i + 5) % 8)) ^ (b >> ((i + 6) % 8))
                   ^ (b >> ((i + 7) % 8)) ^ (0x63 >> i)) & 1) << i
        out.append(v)
    return out


SBOX = _aes_sbox()
assert len(SBOX) == 256 and sorted(SBOX) == list(range(256))

MASK = (1 << 256) - 1


def input_tables():
    # NIST convention: x0 is the most significant bit of the input byte, y0 of the output byte.
    return {f'x{i}': sum(1 << v for v in range(256) if (v >> (7 - i)) & 1) for i in range(8)}


def output_targets():
    return {f'y{i}': sum(1 << v for v in range(256) if (SBOX[v] >> (7 - i)) & 1) for i in range(8)}


def read(path):
    """Return list of gates (op, out, ins) in file order, plus outputs list."""
    gates = []
    in_slp = False
    ren = {}
    for line in open(path):
        s = line.strip()
        m = re.match(r'(Inputs|Outputs):\s*([A-Za-z_]+)(\d+):\2(\d+)', s)
        if m and not in_slp:
            pre, lo, hi = m.group(2), int(m.group(3)), int(m.group(4))
            new = 'x' if m.group(1) == 'Inputs' else 'y'
            if pre != new:
                for k in range(lo, hi + 1):
                    ren[f'{pre}{k}'] = f'{new}{k - lo}'
            continue
        if s.startswith('begin SLP'):
            in_slp = True
            continue
        if s.startswith('end SLP'):
            break
        if not in_slp or not s or s.startswith('%'):
            continue
        tok = s.split('%')[0].split()
        if not tok:
            continue
        op = tok[0].upper()
        gates.append((op, ren.get(tok[1], tok[1]), tuple(ren.get(t, t) for t in tok[2:])))
    return gates


def write(path, gates, name, comment=()):
    ints = [g[1] for g in gates if not re.fullmatch(r'y\d', g[1])]
    with open(path, 'w', newline='\n') as f:
        f.write('%NCFF-0.1-2026 (NIST Circuit File Format)\n\n')
        for c in comment:
            f.write(f'  % {c}\n')
        f.write(f'\nbegin circuit {name}\n\n')
        f.write('Inputs: x0:x7\nOutputs: y0:y7\n')
        f.write('Internal: ' + ' '.join(ints) + '\n')
        f.write('GateSyntax: GateName Output Inputs\n\nbegin SLP\n')
        for op, o, ins in gates:
            f.write(f'{op} {o} {" ".join(ins)}\n')
        f.write('end SLP\nend circuit\n')


def simulate(gates):
    v = dict(input_tables())
    for op, o, ins in gates:
        a = [v[i] for i in ins]
        if op == 'AND':
            r = a[0] & a[1]
        elif op == 'XOR':
            r = a[0] ^ a[1]
        elif op == 'XNOR':
            r = (a[0] ^ a[1]) ^ MASK
        elif op == 'NOT':
            r = a[0] ^ MASK
        else:
            raise ValueError(op)
        v[o] = r
    return v


def correct(gates):
    v = simulate(gates)
    t = output_targets()
    return all(v.get(k) == t[k] for k in t)


def metrics(gates):
    lvl = {f'x{i}': 0 for i in range(8)}
    alv = dict(lvl)
    A = 0
    for op, o, ins in gates:
        lvl[o] = 1 + max(lvl[i] for i in ins)
        alv[o] = max(alv[i] for i in ins) + (1 if op == 'AND' else 0)
        A += op == 'AND'
    outs = [f'y{i}' for i in range(8)]
    return A, max(alv[y] for y in outs), len(gates), max(lvl[y] for y in outs)


def symbolic(gates):
    """name -> (frozenset atoms, const)"""
    s = {f'x{i}': (frozenset([f'x{i}']), 0) for i in range(8)}
    for op, o, ins in gates:
        if op == 'AND':
            s[o] = (frozenset([o]), 0)
        elif op in ('XOR', 'XNOR'):
            a, b = s[ins[0]], s[ins[1]]
            s[o] = (a[0] ^ b[0], a[1] ^ b[1] ^ (1 if op == 'XNOR' else 0))
        elif op == 'NOT':
            a = s[ins[0]]
            s[o] = (a[0], a[1] ^ 1)
    return s


def fmt(sym):
    atoms, c = sym
    return ('1+' if c else '') + '+'.join(sorted(atoms, key=lambda t: (t[0], int(t[1:]) if t[1:].isdigit() else t)))
