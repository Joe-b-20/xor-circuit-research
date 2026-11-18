"""Structural Verilog netlists (Yosys and OpenROAD output): parse, simulate, area, activity.

The simulation evaluates every cell through its Liberty function (liberty.py), bit-parallel over
a set of input vectors (all 2^n for n <= 16), and compares the outputs with the design's
reference function.  This check uses neither Yosys nor OpenROAD's view of the cells, so it is
independent of the SAT proof that flow.py runs with Yosys.

Switching activity: with a new independent, uniformly random input every cycle, a net that is 1
for a fraction p of the inputs toggles with probability 2p(1-p) per cycle (zero-delay: glitches
are not counted).  p is exact when all 2^n inputs are simulated.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import liberty as L

_COMMENT = re.compile(r'//[^\n]*|/\*.*?\*/', re.S)
_INST = re.compile(r'^\s*(\\\S+|[A-Za-z_][\w$]*)\s+(\\\S+|[A-Za-z_][\w$]*)\s*\((.*)\)\s*$', re.S)
_CONN = re.compile(r'\.\s*(\w+)\s*\(\s*([^()]*?)\s*\)')
_KEYWORDS = {'module', 'endmodule', 'input', 'output', 'inout', 'wire', 'reg', 'assign',
             'supply0', 'supply1', 'tri'}


def net(s):
    s = s.strip()
    if s.startswith('\\'):
        s = s[1:].strip()
    return re.sub(r'\s+', '', s)


@dataclass
class Instance:
    cell: str
    name: str
    pins: dict          # pin -> net


@dataclass
class Netlist:
    module: str
    instances: list = field(default_factory=list)
    assigns: list = field(default_factory=list)      # (lhs net, rhs net)


def parse(text):
    text = _COMMENT.sub('', text)
    nl = None
    for stmt in text.split(';'):
        s = stmt.strip()
        if not s:
            continue
        if s.startswith('endmodule'):
            s = s[len('endmodule'):].strip()
            if not s:
                continue
        word = s.split(None, 1)[0]
        if word == 'module':
            if nl is not None:
                raise ValueError('more than one module in the netlist')
            nl = Netlist(s.split(None, 1)[1].split('(')[0].strip())
            continue
        if word == 'assign':
            lhs, rhs = s[len('assign'):].split('=', 1)
            nl.assigns.append((net(lhs), net(rhs)))
            continue
        if word in _KEYWORDS:
            continue
        m = _INST.match(s)
        if not m:
            raise ValueError('cannot read netlist statement: %r' % s[:120])
        pins = {p: net(n) for p, n in _CONN.findall(m.group(3))}
        nl.instances.append(Instance(net(m.group(1)), net(m.group(2)), pins))
    if nl is None:
        raise ValueError('no module in the netlist')
    return nl


def _const(n, ones):
    m = re.fullmatch(r"1'[bh]([01])", n)
    if m:
        return ones if m.group(1) == '1' else 0
    return None


@dataclass
class Simulation:
    count: int                 # vectors simulated
    exhaustive: bool
    mismatches: int            # output bits x vectors that differ from the reference
    first_mismatch: object
    tables: dict               # net -> table
    area_logic: float
    area_physical: float
    cells: dict                # cell name -> count (logic cells)
    physical_cells: dict


def simulate(nl, lib, d, xs, physical=()):
    """Simulate netlist ``nl`` (cells of ``lib``) on bus inputs ``xs``; compare with design d."""
    count = len(xs)
    ones = (1 << count) - 1
    val = {}
    for k in range(d.n_in):
        t = 0
        for i, x in enumerate(xs):
            if (x >> k) & 1:
                t |= 1 << i
        val['x[%d]' % k] = t
    driver = {}
    compiled = {}
    cells, phys = {}, {}
    area_logic = area_phys = 0.0
    for inst in nl.instances:
        c = lib.cells.get(inst.cell)
        if c is None and inst.cell.startswith(tuple(physical)) and not inst.pins:
            phys[inst.cell] = phys.get(inst.cell, 0) + 1      # LEF-only cell (tap): no logic
            continue
        if c is None:
            raise ValueError('cell %s is not in library %s' % (inst.cell, lib.name))
        if c.sequential:
            raise ValueError('sequential cell %s in a combinational netlist' % inst.cell)
        if not c.outputs or inst.cell.startswith(tuple(physical)):
            phys[inst.cell] = phys.get(inst.cell, 0) + 1
            area_phys += c.area
            continue
        cells[inst.cell] = cells.get(inst.cell, 0) + 1
        area_logic += c.area
        for p in c.outputs:
            n = inst.pins.get(p.name)
            if n:
                if n in driver:
                    raise ValueError('net %s has two drivers' % n)
                driver[n] = (inst, p)
    alias = dict(nl.assigns)

    state = {}

    def value(n):
        cv = _const(n, ones)
        if cv is not None:
            return cv
        if n in val:
            return val[n]
        if state.get(n) == 1:
            raise ValueError('combinational loop through %s' % n)
        state[n] = 1
        if n in driver:
            inst, p = driver[n]
            key = (inst.cell, p.name)
            if key not in compiled:
                compiled[key] = L.compile_function(p.function)
            fn, names = compiled[key]
            ins = {}
            for a in names:
                if a not in inst.pins:
                    raise ValueError('%s %s: input pin %s unconnected' % (inst.cell, inst.name, a))
                ins[a] = value(inst.pins[a])
            v = fn(ins, ones)
        elif n in alias:
            v = value(alias[n])
        else:
            raise ValueError('net %s has no driver' % n)
        val[n] = v
        state[n] = 2
        return v

    mismatches = 0
    first = None
    expected = [d.value(x) for x in xs]
    for r in range(d.n_out):
        got = value('y[%d]' % r)
        want = 0
        for i, y in enumerate(expected):
            if (y >> r) & 1:
                want |= 1 << i
        diff = got ^ want
        if diff:
            mismatches += bin(diff).count('1')
            if first is None:
                i = (diff & -diff).bit_length() - 1
                first = {'x': xs[i], 'output_bit': r, 'expected': (want >> i) & 1}
    for n in driver:          # nets that drive nothing reachable from outputs still get tables
        value(n)
    return Simulation(count, count == 1 << d.n_in, mismatches, first, val, area_logic, area_phys,
                      cells, phys)


def activity(sim):
    """net -> (toggles per cycle, duty) under independent uniformly random inputs (zero delay)."""
    out = {}
    for n, t in sim.tables.items():
        p = bin(t).count('1') / sim.count
        out[n] = (2.0 * p * (1.0 - p), p)
    return out
