"""A small Liberty reader: per cell its area, pins (direction, capacitance, function).

Only what the benchmark needs is read; groups other than ``library``/``cell``/``pin`` are
skipped (bus/bundle pins are not supported, and no cell the flows use has them).  Functions are
parsed into evaluators over bit-parallel truth tables (Python ints), which is how mapped and
routed netlists are simulated exhaustively without Yosys (see netlist.py).

Function syntax (Liberty): ``!a`` or ``a'`` NOT, ``^`` XOR, ``&``/``*``/juxtaposition AND,
``|``/``+`` OR, parentheses, constants 0 and 1.  Precedence, high to low: NOT, XOR, AND, OR.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
from dataclasses import dataclass, field

_TOKEN = re.compile(r'''
    (?P<comment>/\*.*?\*/)
  | (?P<string>"(?:[^"\\]|\\.)*")
  | (?P<cont>\\\n)
  | (?P<punct>[{}();:,])
  | (?P<word>[^\s{}();:,"]+)
  | (?P<ws>\s+)
''', re.S | re.X)


@dataclass
class Pin:
    name: str
    direction: str = ''
    capacitance: float = 0.0
    function: str = ''


@dataclass
class Cell:
    name: str
    area: float = 0.0
    pins: dict = field(default_factory=dict)
    dont_use: bool = False
    sequential: bool = False

    @property
    def inputs(self):
        return [p for p in self.pins.values() if p.direction == 'input']

    @property
    def outputs(self):
        return [p for p in self.pins.values() if p.direction == 'output']


@dataclass
class Library:
    name: str
    cells: dict
    cap_unit: str        # 'ff' or 'pf'
    time_unit: str

    def cap_in_lib_units(self, femtofarads):
        return femtofarads * {'ff': 1.0, 'pf': 1e-3}[self.cap_unit]


def _tokens(text):
    for m in _TOKEN.finditer(text):
        k = m.lastgroup
        if k in ('comment', 'ws', 'cont'):
            continue
        yield k, m.group(k)


def parse(text):
    """Parse a Liberty file into a Library (cells, pins; other groups skipped)."""
    toks = list(_tokens(text))
    i = 0
    n = len(toks)
    lib = Library('', {}, 'ff', '1ns')
    stack = []            # (group type, name, object)

    def unq(s):
        return s[1:-1] if s.startswith('"') else s

    while i < n:
        kind, val = toks[i]
        if val == '}':
            stack.pop()
            i += 1
            continue
        # statement: word followed by ':' (simple attribute) or '(' (group or complex attribute)
        if i + 1 < n and toks[i + 1][1] == ':':
            j = i + 2
            vals = []
            while j < n and toks[j][1] not in (';', '}'):
                vals.append(unq(toks[j][1]))
                j += 1
            value = ' '.join(vals)
            top = stack[-1] if stack else None
            if top:
                gt, _, obj = top
                if gt == 'cell':
                    if val == 'area':
                        obj.area = float(value)
                    elif val == 'dont_use':
                        obj.dont_use = value.lower() == 'true'
                elif gt == 'pin':
                    if val == 'direction':
                        obj.direction = value
                    elif val == 'capacitance':
                        obj.capacitance = float(value)
                    elif val == 'function':
                        obj.function = value
                elif gt == 'library' and val == 'time_unit':
                    lib.time_unit = value
            i = j + 1 if j < n and toks[j][1] == ';' else j
            continue
        if i + 1 < n and toks[i + 1][1] == '(':
            j = i + 2
            args = []
            while toks[j][1] != ')':
                if toks[j][1] != ',':
                    args.append(unq(toks[j][1]))
                j += 1
            j += 1
            if j < n and toks[j][1] == '{':
                gname = args[0] if args else ''
                parent = stack[-1] if stack else None
                obj = None
                if val == 'library':
                    lib.name = gname
                    obj = lib
                elif val == 'cell' and parent and parent[0] == 'library':
                    obj = Cell(gname)
                    lib.cells[gname] = obj
                elif val == 'pin' and parent and parent[0] == 'cell':
                    obj = Pin(gname)
                    parent[2].pins[gname] = obj
                elif val in ('ff', 'latch', 'statetable', 'ff_bank', 'latch_bank') and parent \
                        and parent[0] == 'cell':
                    parent[2].sequential = True
                stack.append((val if obj is not None else '-', gname, obj))
                i = j + 1
            else:
                if val == 'capacitive_load_unit' and len(args) == 2:
                    if float(args[0]) != 1.0:
                        raise ValueError('capacitive_load_unit multiplier %s' % args[0])
                    lib.cap_unit = args[1].lower()
                i = j + 1 if j < n and toks[j][1] == ';' else j
            continue
        i += 1
    return lib


# ---- functions ---------------------------------------------------------------------------

_FTOK = re.compile(r"\s*(?:([A-Za-z_][A-Za-z_0-9\[\]\.]*)|([01])|(.))")


def compile_function(expr):
    """Parse a Liberty function; returns (evaluate(values: dict, ones: int) -> int, pin names)."""
    toks = []
    for m in _FTOK.finditer(expr):
        if m.group(1):
            toks.append(('id', m.group(1)))
        elif m.group(2):
            toks.append(('c', int(m.group(2))))
        elif m.group(3) and not m.group(3).isspace():
            toks.append(('op', m.group(3)))
    pos = [0]
    names = set()

    def peek():
        return toks[pos[0]] if pos[0] < len(toks) else (None, None)

    def take():
        t = toks[pos[0]]
        pos[0] += 1
        return t

    def primary():
        k, v = take()
        if k == 'op' and v == '!':
            f = primary()
            node = ('not', f)
        elif k == 'op' and v == '(':
            node = or_expr()
            k2, v2 = take()
            if v2 != ')':
                raise ValueError('bad function %r' % expr)
        elif k == 'id':
            names.add(v)
            node = ('id', v)
        elif k == 'c':
            node = ('c', v)
        else:
            raise ValueError('bad function %r' % expr)
        while peek() == ('op', "'"):
            take()
            node = ('not', node)
        return node

    def xor_expr():
        node = primary()
        while peek() == ('op', '^'):
            take()
            node = ('xor', node, primary())
        return node

    def and_expr():
        node = xor_expr()
        while True:
            k, v = peek()
            if (k, v) in (('op', '&'), ('op', '*')):
                take()
                node = ('and', node, xor_expr())
            elif k in ('id', 'c') or (k, v) in (('op', '!'), ('op', '(')):
                node = ('and', node, xor_expr())       # juxtaposition
            else:
                return node

    def or_expr():
        node = and_expr()
        while peek() in (('op', '|'), ('op', '+')):
            take()
            node = ('or', node, and_expr())
        return node

    tree = or_expr()
    if pos[0] != len(toks):
        raise ValueError('bad function %r' % expr)

    def ev(node, vals, ones):
        t = node[0]
        if t == 'id':
            return vals[node[1]]
        if t == 'c':
            return ones if node[1] else 0
        if t == 'not':
            return ones ^ ev(node[1], vals, ones)
        a, b = ev(node[1], vals, ones), ev(node[2], vals, ones)
        return a & b if t == 'and' else a | b if t == 'or' else a ^ b

    return (lambda vals, ones: ev(tree, vals, ones)), sorted(names)


def load(path, cache_dir=None):
    """Parse (with a JSON cache, keyed by the file's and this parser's content)."""
    path = pathlib.Path(path)
    if cache_dir:
        key = hashlib.sha256(path.read_bytes() + pathlib.Path(__file__).read_bytes()).hexdigest()
        cache = pathlib.Path(cache_dir) / ('%s.%s.json' % (path.name, key[:16]))
        if cache.exists():
            return _from_json(json.loads(cache.read_text()))
    lib = parse(path.read_text())
    if cache_dir:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(_to_json(lib)))
    return lib


def _to_json(lib):
    return {'name': lib.name, 'cap_unit': lib.cap_unit, 'time_unit': lib.time_unit,
            'cells': {c.name: {'area': c.area, 'dont_use': c.dont_use, 'seq': c.sequential,
                               'pins': {p.name: [p.direction, p.capacitance, p.function]
                                        for p in c.pins.values()}}
                      for c in lib.cells.values()}}


def _from_json(j):
    cells = {}
    for name, c in j['cells'].items():
        cell = Cell(name, c['area'], {}, c['dont_use'], c['seq'])
        for pn, (dr, cap, fn) in c['pins'].items():
            cell.pins[pn] = Pin(pn, dr, cap, fn)
        cells[name] = cell
    return Library(j['name'], cells, j['cap_unit'], j['time_unit'])
