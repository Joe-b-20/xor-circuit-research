"""Circuits over a configurable gate library: representation, file formats, evaluation, metrics.

A circuit has ``n`` inputs and an ordered list of gates; signal ``i < n`` is input ``i`` and
signal ``n + j`` is gate ``j``.  A gate is ``(op, a, b)`` where ``op`` is the 4-bit truth table
of a two-input function, ``f(a, b) = (op >> ((a << 1) | b)) & 1``; the unary NOT is op 3 with
``b == a``.  Outputs are signal numbers.

Bit order (the same as NIST's AES files, "msb/msb"): input ``i`` is bit ``n-1-i`` of the input
integer ``x`` and output ``j`` is bit ``m-1-j`` of the output integer.  A truth table is a
Python int whose bit ``x`` is the signal's value at input ``x``.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

# name -> (op code, arity); ANDN o a b = a & ~b, ORN o a b = a | ~b (second operand complemented)
OPS = {'AND': 8, 'OR': 14, 'XOR': 6, 'XNOR': 9, 'NAND': 7, 'NOR': 1, 'ANDN': 4, 'ORN': 13,
       'NOT': 3}
OPNAME = {v: k for k, v in OPS.items()}
NONLINEAR_OPS = {8, 14, 7, 1, 4, 13, 2, 11}
SYMMETRIC = {8, 14, 6, 9, 7, 1}

HERE = Path(__file__).resolve().parent
MODELS = HERE / 'models'


def op_apply(op, a, b, ones):
    """Bitwise op on truth tables (ints), result masked to ``ones``."""
    r = 0
    if op & 1: r |= ~a & ~b
    if op & 2: r |= ~a & b
    if op & 4: r |= a & ~b
    if op & 8: r |= a & b
    return r & ones


def canonical(op, a, b):
    """Rewrite the mirrored asymmetric ops (~a&b, ~a|b) and unary forms to library ops."""
    if op == 2: return 4, b, a          # ~a & b  = ANDN(b, a)
    if op == 11: return 13, b, a        # ~a | b  = ORN(b, a)
    if op == 5: return 3, b, b          # ~b
    if op == 3: return 3, a, a
    return op, a, b


@dataclass
class Circuit:
    n: int
    m: int
    gates: list                      # [(op, a, b)]
    outputs: list                    # signal numbers
    name: str = 'circuit'
    in_names: list = field(default_factory=list)
    out_names: list = field(default_factory=list)

    def __post_init__(self):
        if not self.in_names: self.in_names = ['x%d' % i for i in range(self.n)]
        if not self.out_names: self.out_names = ['y%d' % j for j in range(self.m)]

    # ---- evaluation ------------------------------------------------------------------------
    def tables(self):
        """Truth tables of every signal (list of ints)."""
        n = self.n; ones = (1 << (1 << n)) - 1
        vals = input_tables(n)
        for op, a, b in self.gates:
            vals.append(op_apply(op, vals[a], vals[b], ones))
        return vals

    def output_tables(self):
        v = self.tables()
        return [v[s] for s in self.outputs]

    def value_table(self):
        """table[x] = output integer at input x (msb/msb)."""
        outs = self.output_tables(); m = self.m
        return [sum(((t >> x) & 1) << (m - 1 - j) for j, t in enumerate(outs))
                for x in range(1 << self.n)]

    # ---- metrics ---------------------------------------------------------------------------
    def metrics(self, model=None):
        lg = [0] * self.n; la = [0] * self.n
        counts = {}
        cost = 0.0
        for op, a, b in self.gates:
            lg.append(1 + max(lg[a], lg[b]))
            la.append((1 if op in NONLINEAR_OPS else 0) + max(la[a], la[b]))
            nm = OPNAME.get(op, 'OP%d' % op)
            counts[nm] = counts.get(nm, 0) + 1
            if model is not None:
                cost += model.cost.get(op, float('nan'))
        return {'G': len(self.gates), 'A': sum(1 for g in self.gates if g[0] in NONLINEAR_OPS),
                'GD': max((lg[s] for s in self.outputs), default=0),
                'AD': max((la[s] for s in self.outputs), default=0),
                'cost': round(cost, 6) if model is not None else None,
                'counts': dict(sorted(counts.items()))}

    def live(self):
        """Copy without gates unreachable from the outputs."""
        need = [False] * (self.n + len(self.gates))
        for s in self.outputs: need[s] = True
        for j in range(len(self.gates) - 1, -1, -1):
            if need[self.n + j]:
                op, a, b = self.gates[j]; need[a] = True; need[b] = True
        new = list(range(self.n)); gates = []
        for j, (op, a, b) in enumerate(self.gates):
            if need[self.n + j]:
                new.append(self.n + len(gates)); gates.append((op, new[a], new[b]))
            else:
                new.append(None)
        return Circuit(self.n, self.m, gates, [new[s] for s in self.outputs], self.name,
                       self.in_names, self.out_names)


def input_tables(n):
    N = 1 << n
    tabs = []
    for i in range(n):
        bit = n - 1 - i
        t = 0
        for x in range(N):
            if (x >> bit) & 1: t |= 1 << x
        tabs.append(t)
    return tabs


def tables_from_values(n, m, table):
    """Output truth tables (msb/msb) from a value table."""
    outs = []
    for j in range(m):
        sh = m - 1 - j; t = 0
        for x, v in enumerate(table):
            if (v >> sh) & 1: t |= 1 << x
        outs.append(t)
    return outs


# ---- cost models -----------------------------------------------------------------------------
@dataclass
class Model:
    name: str
    gates: dict                     # allowed name -> cost
    not_as: str = 'NOT'             # how a NOT is written: 'NOT' or 'XNOR0' (NIST: XNOR t a 0)
    description: str = ''

    @property
    def cost(self):
        c = {}
        for nm, v in self.gates.items():
            c[OPS[nm]] = v
        return c

    def ops(self):
        return {OPS[nm] for nm in self.gates}

    @classmethod
    def load(cls, name_or_path):
        p = Path(name_or_path)
        if not p.exists(): p = MODELS / ('%s.json' % name_or_path)
        d = json.loads(p.read_text(encoding='utf-8'))
        return cls(d['name'], d['gates'], d.get('not_as', 'NOT'), d.get('description', ''))


# ---- kernel format ---------------------------------------------------------------------------
def to_kernel(c: Circuit) -> str:
    lines = ['n %d' % c.n, 'm %d' % c.m, 'g %d' % len(c.gates)]
    lines += ['%d %d %d' % g for g in c.gates]
    lines.append('o ' + ' '.join(str(s) for s in c.outputs))
    return '\n'.join(lines) + '\n'


def from_kernel(text: str, name='circuit') -> Circuit:
    toks = [ln.split() for ln in text.splitlines() if ln.strip() and not ln.startswith('#')]
    n = int(toks[0][1]); m = int(toks[1][1]); g = int(toks[2][1])
    gates = [tuple(int(t) for t in toks[3 + j]) for j in range(g)]
    outs = [int(t) for t in toks[3 + g][1:]]
    return Circuit(n, m, gates, outs, name)


# ---- NCFF (NIST circuit file format) ---------------------------------------------------------
_RANGE = re.compile(r'^([A-Za-z_][A-Za-z_0-9]*?)(\d+):([A-Za-z_][A-Za-z_0-9]*?)(\d+)$')


def _expand(spec):
    out = []
    for tok in spec.split():
        mm = _RANGE.match(tok)
        if mm and mm.group(1) == mm.group(3):
            lo, hi = int(mm.group(2)), int(mm.group(4))
            step = 1 if hi >= lo else -1
            out += ['%s%d' % (mm.group(1), k) for k in range(lo, hi + step, step)]
        else:
            out.append(tok)
    return out


def read_ncff(path_or_text, name=None) -> Circuit:
    """Read an NCFF / NIST .slp circuit.  Constant operands are folded: XNOR t a 0 -> NOT a,
    XOR t a 1 -> NOT a, XOR t a 0 -> wire alias; other constant uses raise ValueError."""
    text = Path(path_or_text).read_text(encoding='utf-8') if '\n' not in str(path_or_text) else path_or_text
    inputs = outputs = None; body = False; ops = []; cname = name or 'circuit'
    for raw in text.splitlines():
        ln = re.split(r'[%#]', raw, 1)[0].strip()
        if not ln: continue
        low = ln.lower()
        if low.startswith('begin circuit'): cname = name or ln.split(None, 2)[2]; continue
        if low.startswith('inputs:'): inputs = _expand(ln.split(':', 1)[1]); continue
        if low.startswith('outputs:'): outputs = _expand(ln.split(':', 1)[1]); continue
        if low == 'begin slp': body = True; continue
        if low == 'end slp': body = False; continue
        if body: ops.append(ln.split())
    sig = {nm: i for i, nm in enumerate(inputs)}
    n = len(inputs); gates = []
    alias = {}

    def ref(t):
        if t in ('0', '1'): return t
        t = alias.get(t, t)
        return sig[t] if not isinstance(t, int) else t

    for tok in ops:
        op = tok[0].upper(); out = tok[1]; args = [ref(a) for a in tok[2:]]
        if op in ('BUF',):
            alias[out] = args[0] if isinstance(args[0], int) else None; continue
        if op == 'NOT':
            code, a, b = 3, args[0], args[0]
        else:
            code = OPS[op]; a, b = args
        consts = [x for x in (a, b) if isinstance(x, str)]
        if consts:
            if code not in (6, 9) or len(consts) == 2:
                raise ValueError('constant operand in %s' % ' '.join(tok))
            c = int(consts[0]); v = b if isinstance(a, str) else a
            if (code == 6 and c == 0) or (code == 9 and c == 1):
                alias[out] = v; continue
            code, a, b = 3, v, v
        code, a, b = canonical(code, a, b)
        sig[out] = n + len(gates); gates.append((code, a, b))
    outs = [alias.get(o, sig.get(o)) for o in outputs]
    if any(o is None for o in outs): raise ValueError('unassigned output')
    return Circuit(n, len(outputs), gates, outs, cname, list(inputs), list(outputs))


def write_ncff(c: Circuit, model: Model | None = None, comments=()) -> str:
    """NCFF text.  Gate wires are t1..; an output's wire takes its output name when the output
    is the only output driven by that gate; outputs equal to an input or to another output's
    gate are written as BUF (zero cost, accepted by the independent verifier)."""
    m = c.metrics(model)
    name_of = {i: c.in_names[i] for i in range(c.n)}
    out_owner = {}
    for j, s in enumerate(c.outputs):
        if s >= c.n and s not in out_owner: out_owner[s] = c.out_names[j]
    lines_body = []; k = 0
    lv = [0] * c.n
    for j, (op, a, b) in enumerate(c.gates):
        s = c.n + j
        nm = out_owner.get(s)
        if nm is None: k += 1; nm = 't%d' % k
        name_of[s] = nm
        lv.append(1 + max(lv[a], lv[b]))
        if op == 3:
            if model is not None and model.not_as == 'XNOR0':
                lines_body.append('XNOR %s %s 0' % (nm, name_of[a]))
            else:
                lines_body.append('NOT %s %s' % (nm, name_of[a]))
        else:
            lines_body.append('%s %s %s %s' % (OPNAME[op], nm, name_of[a], name_of[b]))
    for j, s in enumerate(c.outputs):
        if name_of.get(s) != c.out_names[j]:
            lines_body.append('BUF %s %s' % (c.out_names[j], name_of[s]))
    internal = ['t%d' % i for i in range(1, k + 1)]
    head = ['%NCFF-0.1-2026 (NIST Circuit File Format), written by nonlinear/boolflux', '',
            'begin circuit %s' % c.name, '']
    for cm in comments: head.append('  %% %s' % cm)
    head.append('  %% Tally: G=%d A=%d GD=%d AD=%d %s%s' % (
        m['G'], m['A'], m['GD'], m['AD'],
        ' '.join('%s=%d' % kv for kv in m['counts'].items()),
        ('; cost %s under model %s' % (m['cost'], model.name)) if model else ''))
    head += ['', 'Inputs: ' + ' '.join(c.in_names), 'Outputs: ' + ' '.join(c.out_names)]
    if internal: head.append('Internal: t1:t%d' % k)
    head += ['GateSyntax: GateName Output Inputs', '', 'begin SLP']
    return '\n'.join(head + lines_body + ['end SLP', 'end circuit']) + '\n'
