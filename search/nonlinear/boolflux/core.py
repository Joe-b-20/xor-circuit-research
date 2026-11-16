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
        outs = self.output_tables(); m = self.m; N = 1 << self.n
        cols = [format(t, 'b').zfill(N)[::-1] for t in outs]
        return [int(''.join(c[x] for c in cols), 2) for x in range(N)]

    # ---- metrics ---------------------------------------------------------------------------
    def metrics(self, model=None):
        lg = [0] * self.n; la = [0] * self.n
        counts = {}
        cost = 0.0
        cost_of = model.cost if model is not None else None      # built once (it was rebuilt for every gate)
        for op, a, b in self.gates:
            lg.append(1 + max(lg[a], lg[b]))
            la.append((1 if op in NONLINEAR_OPS else 0) + max(la[a], la[b]))
            nm = OPNAME.get(op, 'OP%d' % op)
            counts[nm] = counts.get(nm, 0) + 1
            if cost_of is not None:
                cost += cost_of.get(op, float('nan'))
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


_INPUT_TABLES = {}


def input_tables(n):
    """Truth tables of the n inputs (a new list on every call; the tables are computed once per n:
    the 2^n-step loop was most of the time of evaluating a small circuit)."""
    tabs = _INPUT_TABLES.get(n)
    if tabs is None:
        N = 1 << n
        tabs = []
        for i in range(n):
            bit = n - 1 - i
            t = 0
            for x in range(N):
                if (x >> bit) & 1: t |= 1 << x
            tabs.append(t)
        tabs = _INPUT_TABLES[n] = tuple(tabs)
    return list(tabs)


def tables_from_values(n, m, table):
    """Output truth tables (msb/msb) from a value table."""
    outs = []
    for j in range(m):
        sh = m - 1 - j
        bits = ''.join('1' if (v >> sh) & 1 else '0' for v in reversed(table))
        outs.append(int(bits, 2))
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
        d = json.loads(model_path(name_or_path).read_text(encoding='utf-8'))
        # the checks independent/verify.py makes, plus a consistent NOT convention
        import math
        for nm, c in d['gates'].items():
            if nm not in OPS or nm == 'BUF':
                raise SystemExit('model %s: unknown or unsupported gate %r' % (d.get('name'), nm))
            if not isinstance(c, (int, float)) or not math.isfinite(c) or c < 0:
                raise SystemExit('model %s: gate %s has cost %r (must be finite and >= 0)' % (d.get('name'), nm, c))
        if d.get('not_as', 'NOT') not in ('NOT', 'XNOR0'):      # a typo must not silently mean 'NOT'
            raise SystemExit('model %s: not_as must be "NOT" or "XNOR0", got %r' % (d.get('name'), d.get('not_as')))
        if d.get('not_as') == 'XNOR0' and 'NOT' in d['gates'] and d['gates'].get('XNOR') != d['gates']['NOT']:
            raise SystemExit('model %s: NOT is written as XNOR(x, 0), so NOT and XNOR must cost the same' % d.get('name'))
        return cls(d['name'], d['gates'], d.get('not_as', 'NOT'), d.get('description', ''))


def model_path(name_or_path):
    """A stock model name (models/<name>.json) first; otherwise a path to a .json file.  A file or
    directory in the current directory that happens to have a model's name is not a model."""
    stock = MODELS / ('%s.json' % name_or_path)
    if stock.exists() and '/' not in str(name_or_path) and not str(name_or_path).endswith('.json'):
        return stock
    p = Path(name_or_path)
    if p.is_file() and p.suffix == '.json':
        return p
    raise SystemExit('unknown model %r (stock models: %s; or a path to a .json model file)'
                     % (name_or_path, ', '.join(sorted(f.stem for f in MODELS.glob('*.json')))))


# ---- kernel format ---------------------------------------------------------------------------
def to_kernel(c: Circuit) -> str:
    lines = ['n %d' % c.n, 'm %d' % c.m, 'g %d' % len(c.gates)]
    lines += ['%d %d %d' % g for g in c.gates]
    lines.append('o ' + ' '.join(str(s) for s in c.outputs))
    return '\n'.join(lines) + '\n'


def from_kernel(text: str, name='circuit') -> Circuit:
    """Read the kernel's .bfx text.  The structure is checked: a truncated file, a
    forward or negative operand or an output outside the circuit raises ValueError instead of
    giving an IndexError later or, for negative numbers, a silently different circuit."""
    toks = [ln.split() for ln in text.splitlines() if ln.strip() and not ln.startswith('#')]
    try:
        if [t[0] for t in toks[:3]] != ['n', 'm', 'g']: raise ValueError('header lines n, m, g expected')
        n = int(toks[0][1]); m = int(toks[1][1]); g = int(toks[2][1])
        if len(toks) < 4 + g or toks[3 + g][0] != 'o': raise ValueError('%d gate lines and an o line expected' % g)
        gates = [tuple(int(t) for t in toks[3 + j]) for j in range(g)]
        outs = [int(t) for t in toks[3 + g][1:]]
    except (IndexError, ValueError) as e:
        raise ValueError('bad kernel circuit %s: %s' % (name, e)) from None
    for j, gt in enumerate(gates):
        if len(gt) != 3 or not 0 <= gt[0] <= 15 or not (0 <= gt[1] < n + j and 0 <= gt[2] < n + j):
            raise ValueError('bad kernel circuit %s: gate %d = %s (op 0..15, operands defined earlier)' % (name, j, gt))
    if len(outs) != m or not all(0 <= o < n + g for o in outs):
        raise ValueError('bad kernel circuit %s: %d outputs declared, o line %s' % (name, m, outs))
    return Circuit(n, m, gates, outs, name)


# ---- NCFF (NIST circuit file format) ---------------------------------------------------------
_RANGE = re.compile(r'^([A-Za-z_][A-Za-z_0-9]*?)(\d+):([A-Za-z_][A-Za-z_0-9]*?)(\d+)$')


def _expand(spec):
    """Names of a declaration line.  As independent/verify.py reads them: commas
    separate too, and a range written with a leading zero keeps its digit width (x00:x07)."""
    out = []
    for tok in spec.replace(',', ' ').split():
        mm = _RANGE.match(tok)
        if mm and mm.group(1) == mm.group(3):
            s = mm.group(2)
            width = len(s) if (len(s) > 1 and s.startswith('0')) else 0
            lo, hi = int(s), int(mm.group(4))
            step = 1 if hi >= lo else -1
            out += ['%s%s' % (mm.group(1), str(k).zfill(width)) for k in range(lo, hi + step, step)]
        else:
            out.append(tok)
    return out


def read_ncff(path_or_text, name=None) -> Circuit:
    """Read an NCFF / NIST .slp circuit.  Constant operands are folded: XNOR t a 0 -> NOT a,
    XOR t a 1 -> NOT a, XOR t a 0 -> wire alias; other constant uses raise ValueError."""
    text = Path(path_or_text).read_text(encoding='utf-8') if '\n' not in str(path_or_text) else path_or_text
    inputs = outputs = None; body = False; ops = []; cname = name or 'circuit'; ncirc = 0
    for raw in text.splitlines():
        ln = re.split(r'[%#]', raw, 1)[0].strip()
        if not ln: continue
        low = ln.lower()
        if low.startswith('begin circuit'):
            ncirc += 1
            if ncirc > 1: break                  # the first circuit only, as independent/verify.py
            cname = name or (ln.split(None, 2) + ['circuit'])[2]; continue
        if low.startswith('inputs:'): inputs = (inputs or []) + _expand(ln.split(':', 1)[1]); continue
        if low.startswith('outputs:'): outputs = (outputs or []) + _expand(ln.split(':', 1)[1]); continue
        if low == 'begin slp': body = True; continue
        if low == 'end slp': body = False; continue
        if body: ops.append(ln.split())
    # malformed files give a ValueError that names the problem (not a TypeError / KeyError, or, for a
    # wire assigned twice, silently the later definition)
    if not inputs or not outputs:
        raise ValueError('circuit %s: no Inputs: or no Outputs: line' % cname)
    if len(set(inputs)) != len(inputs):
        raise ValueError('circuit %s: an input is declared twice' % cname)
    sig = {nm: i for i, nm in enumerate(inputs)}
    n = len(inputs); gates = []
    alias = {}

    def ref(t, tok):
        if t in ('0', '1'): return t
        if t in alias:
            if alias[t] is None: raise ValueError('constant wire used in %s' % ' '.join(tok))
            return alias[t]
        if t not in sig: raise ValueError('operand %s is not defined before %s' % (t, ' '.join(tok)))
        return sig[t]

    for tok in ops:
        op = tok[0].upper()
        if op not in OPS and op != 'BUF':
            raise ValueError('unknown gate %s' % ' '.join(tok))
        if len(tok) != (3 if op in ('NOT', 'BUF') else 4):
            raise ValueError('wrong number of operands in %s' % ' '.join(tok))
        out = tok[1]; args = [ref(a, tok) for a in tok[2:]]
        if out in sig or out in alias or out in ('0', '1'):
            raise ValueError('wire %s is assigned twice (or is an input) in %s' % (out, ' '.join(tok)))
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
    if any(o is None for o in outs): raise ValueError('unassigned (or constant) output')
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
    # internal wires are t1, t2, ... unless an input or output already has such a name
    # (then t_1, t__1, ...); a collision would give a file that reads back as another circuit
    taken = set(c.in_names) | set(c.out_names)
    if len(taken) != c.n + c.m or taken & {'0', '1'}:
        raise ValueError('write_ncff: input/output names must be distinct and not 0 or 1')
    pre = 't'
    while any(re.fullmatch(re.escape(pre) + r'\d+', x) for x in taken): pre += '_'
    for j, (op, a, b) in enumerate(c.gates):
        s = c.n + j
        nm = out_owner.get(s)
        if nm is None: k += 1; nm = '%s%d' % (pre, k)
        name_of[s] = nm
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
    head = ['%NCFF-0.1-2026 (NIST Circuit File Format), written by search/nonlinear/boolflux', '',
            'begin circuit %s' % c.name, '']
    for cm in comments: head.append('  %% %s' % cm)
    counts = dict(m['counts'])
    if model is not None and model.not_as == 'XNOR0' and 'NOT' in counts:
        counts['XNOR'] = counts.get('XNOR', 0) + counts.pop('NOT')
        counts = dict(sorted(counts.items()))
    head.append('  %% Tally: G=%d A=%d GD=%d AD=%d %s%s' % (
        m['G'], m['A'], m['GD'], m['AD'],
        ' '.join('%s=%d' % kv for kv in counts.items()),
        ('; cost %s under model %s' % (m['cost'], model.name)) if model else ''))
    head += ['', 'Inputs: ' + ' '.join(c.in_names), 'Outputs: ' + ' '.join(c.out_names)]
    if k: head.append('Internal: %s1:%s%d' % (pre, pre, k))
    head += ['GateSyntax: GateName Output Inputs', '', 'begin SLP']
    return '\n'.join(head + lines_body + ['end SLP', 'end circuit']) + '\n'
