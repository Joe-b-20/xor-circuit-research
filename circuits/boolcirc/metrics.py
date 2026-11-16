"""NIST's complexity metrics of a circuit, and the file names that encode them.

NIST's circuit list and file names use four metrics (the header of every 2026 file states the
syntax ``<basename>-aA-adAD-gG-gdGD-xxX-Y``):

    A   #AND        number of nonlinear gates (AND; NAND, OR, NOR count the same)
    AD  AND depth   most nonlinear gates on any input-to-output path
    G   #Gates      every gate, NOT included
    GD  gate depth  longest input-to-output path in gates, inputs at depth 0, NOT counted
    X   #XOR + #XNOR,   Y  #XNOR   (two more numbers in the names)

The 2020 names write ``-gG-aA-dGD-adAD``.  Depth rules NIST's pages leave implicit (NOT gates,
inputs at depth 0) are stated here as this module's definitions and are confirmed against the
per-level tallies NIST writes in its 2026 files (``check_tallies``): every imported file agrees.

``metrics`` computes the whole set, with the per-level tallies, the depth of every wire and the
dead gates (gates no output depends on).  Gate depth is taken over all gates; ``live_gate_depth``
over the outputs only (they differ only when dead gates exist, which the check reports).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .ncff import CONSTANTS, NONLINEAR

_NAME_2026 = re.compile(r'-a(\d+)-ad(\d+)-g(\d+)-gd(\d+)-xx(\d+)-(\d+)(?:[.-]|$)')
# names from November 2026 on (NIST commit e6ac0d0): -xxnX-Y-Z, X = XOR + XNOR + NOT, Y = XNOR, Z = NOT
_NAME_2026N = re.compile(r'-a(\d+)-ad(\d+)-g(\d+)-gd(\d+)-xxn(\d+)-(\d+)-(\d+)(?:[.-]|$)')
_NAME_2020 = re.compile(r'-g(\d+)-a(\d+)-d(\d+)-ad(\d+)(?:[.-]|$)', re.IGNORECASE)


@dataclass
class Metrics:
    """The metrics of one circuit (see the module docstring)."""
    and_count: int
    and_depth: int
    gates: int
    gate_depth: int
    xor: int
    xnor: int
    not_count: int = 0
    other: dict = field(default_factory=dict)      # NAND/OR/NOR counts, if any
    gate_levels: list = field(default_factory=list)  # gates at gate level 1, 2, ...
    and_levels: list = field(default_factory=list)   # nonlinear gates at AND level 1, 2, ...
    depth: dict = field(default_factory=dict)        # wire -> gate depth
    and_depth_of: dict = field(default_factory=dict)  # wire -> AND depth
    dead: list = field(default_factory=list)         # gate outputs no output depends on
    live_gate_depth: int = 0
    live_and_depth: int = 0

    @property
    def xx(self):
        """#XOR + #XNOR."""
        return self.xor + self.xnor

    def tuple(self):
        """(A, AD, G, GD), NIST's primary tuple."""
        return (self.and_count, self.and_depth, self.gates, self.gate_depth)

    def name_suffix(self):
        """``-aA-adAD-gG-gdGD-xxX-Y`` for this circuit."""
        return '-a%d-ad%d-g%d-gd%d-xx%d-%d' % (self.and_count, self.and_depth, self.gates,
                                               self.gate_depth, self.xx, self.xnor)

    def summary(self):
        return 'A=%d AD=%d G=%d GD=%d XX=%d (XOR %d, XNOR %d%s)' % (
            self.and_count, self.and_depth, self.gates, self.gate_depth, self.xx, self.xor,
            self.xnor, ', NOT %d' % self.not_count if self.not_count else '')


def metrics(circuit):
    """Compute every metric of a validated circuit."""
    depth = {w: 0 for w in circuit.inputs}
    adepth = {w: 0 for w in circuit.inputs}
    counts = {}
    gate_levels = {}
    and_levels = {}
    for c in CONSTANTS:                      # literal operands sit at depth 0
        depth.setdefault(c, 0)
        adepth.setdefault(c, 0)
    for g in circuit.gates:
        d = 1 + max(depth[a] for a in g.args)
        nl = g.op in NONLINEAR
        ad = max(adepth[a] for a in g.args) + (1 if nl else 0)
        depth[g.out] = d
        adepth[g.out] = ad
        counts[g.op] = counts.get(g.op, 0) + 1
        gate_levels[d] = gate_levels.get(d, 0) + 1
        if nl:
            and_levels[ad] = and_levels.get(ad, 0) + 1
    # dead gates: no output depends on them
    live = set(circuit.outputs)
    for g in reversed(circuit.gates):
        if g.out in live:
            live.update(g.args)
    dead = [g.out for g in circuit.gates if g.out not in live]
    gd = max((depth[g.out] for g in circuit.gates), default=0)
    ad_all = max((adepth[g.out] for g in circuit.gates), default=0)
    out_gd = max((depth[o] for o in circuit.outputs), default=0)
    out_ad = max((adepth[o] for o in circuit.outputs), default=0)
    other = {k: v for k, v in counts.items() if k in ('NAND', 'OR', 'NOR')}
    for c in CONSTANTS:
        depth.pop(c, None)
        adepth.pop(c, None)
    return Metrics(
        and_count=sum(counts.get(k, 0) for k in NONLINEAR),
        and_depth=ad_all,
        gates=len(circuit.gates),
        gate_depth=gd,
        xor=counts.get('XOR', 0),
        xnor=counts.get('XNOR', 0),
        not_count=counts.get('NOT', 0),
        other=other,
        gate_levels=[gate_levels.get(i, 0) for i in range(1, gd + 1)],
        and_levels=[and_levels.get(i, 0) for i in range(1, ad_all + 1)],
        depth=depth,
        and_depth_of=adepth,
        dead=dead,
        live_gate_depth=out_gd,
        live_and_depth=out_ad,
    )


def name_metrics(name):
    """Metrics encoded in a NIST file or circuit name, as a dict, or None.

    Keys: ``A``, ``AD``, ``G``, ``GD`` always; ``XX`` and ``XNOR`` for 2026 names.
    """
    m = _NAME_2026N.search(name)
    if m:
        a, ad, g, gd, xxn, y, z = map(int, m.groups())
        return {'A': a, 'AD': ad, 'G': g, 'GD': gd, 'XX': xxn - z, 'XNOR': y, 'NOT': z, 'style': '2026n'}
    m = _NAME_2026.search(name)
    if m:
        a, ad, g, gd, xx, y = map(int, m.groups())
        return {'A': a, 'AD': ad, 'G': g, 'GD': gd, 'XX': xx, 'XNOR': y, 'style': '2026'}
    m = _NAME_2020.search(name)
    if m:
        g, a, d, ad = map(int, m.groups())
        return {'A': a, 'AD': ad, 'G': g, 'GD': d, 'style': '2020'}
    return None


def check_name(name, m):
    """Mismatches between a name's numbers and computed metrics (empty list: they agree).

    Returns ``['no metrics in name']`` when the name encodes none.
    """
    want = name_metrics(name)
    if want is None:
        return ['no metrics in name']
    have = {'A': m.and_count, 'AD': m.and_depth, 'G': m.gates, 'GD': m.gate_depth,
            'XX': m.xx, 'XNOR': m.xnor, 'NOT': m.not_count}
    return ['%s: name says %d, circuit has %d' % (k, want[k], have[k])
            for k in ('A', 'AD', 'G', 'GD', 'XX', 'XNOR', 'NOT') if k in want and want[k] != have[k]]


_TALLY_GATES = re.compile(r'Tally of gates \((\d+)\):\s*(.*)')
_DEPTHS = re.compile(r'Gate depth (\d+); AND depth (\d+)')
_DEPTHS_2020 = re.compile(r'Depth\(Gate\):\s*(\d+);\s*Depth\(AND\):\s*(\d+)')
_PER_GATE_LEVEL = re.compile(r'Gates per gate level:\s*([\d ]+)')
_PER_AND_LEVEL = re.compile(r'AND gates per AND level:\s*([\d ]+)')
_TALLY_2020 = re.compile(r'Tally:\s*(\d+) inputs, (\d+) outputs, (\d+) gates, (\d+) AND, (\d+) XOR(?:, (\d+) XNOR)?')


def header_tallies(circuit):
    """The tallies NIST wrote in the circuit's header comments, as a dict (empty if none):
    ``gates``, ``by_op`` ({op: count}), ``gate_depth``, ``and_depth``, ``gate_levels``,
    ``and_levels``."""
    out = {}
    for c in circuit.comments:
        m = _TALLY_GATES.search(c)
        if m:
            out['gates'] = int(m.group(1))
            by_op = {}
            for part in m.group(2).split(';'):
                words = part.split()
                if len(words) >= 2 and words[0].isdigit():
                    by_op[words[1].upper()] = int(words[0])
            out['by_op'] = by_op
        m = _TALLY_2020.search(c)
        if m:
            out['gates'] = int(m.group(3))
            out['by_op'] = {'AND': int(m.group(4)), 'XOR': int(m.group(5)),
                            'XNOR': int(m.group(6) or 0)}
        m = _DEPTHS.search(c) or _DEPTHS_2020.search(c)
        if m:
            out['gate_depth'] = int(m.group(1))
            out['and_depth'] = int(m.group(2))
        m = _PER_GATE_LEVEL.search(c)
        if m:
            out['gate_levels'] = list(map(int, m.group(1).split()))
        m = _PER_AND_LEVEL.search(c)
        if m:
            out['and_levels'] = list(map(int, m.group(1).split()))
    return out


def check_tallies(circuit, m):
    """Mismatches between the header tallies of a NIST file and the computed metrics."""
    t = header_tallies(circuit)
    bad = []
    if 'gates' in t and t['gates'] != m.gates:
        bad.append('header: %d gates, circuit has %d' % (t['gates'], m.gates))
    have = {'AND': m.and_count - sum(m.other.values()), 'XOR': m.xor, 'XNOR': m.xnor,
            'NOT': m.not_count, **m.other}
    for op, cnt in t.get('by_op', {}).items():
        if have.get(op, 0) != cnt:
            bad.append('header: %d %s, circuit has %d' % (cnt, op, have.get(op, 0)))
    if 'gate_depth' in t and t['gate_depth'] != m.gate_depth:
        bad.append('header: gate depth %d, circuit has %d' % (t['gate_depth'], m.gate_depth))
    if 'and_depth' in t and t['and_depth'] != m.and_depth:
        bad.append('header: AND depth %d, circuit has %d' % (t['and_depth'], m.and_depth))
    if 'gate_levels' in t and t['gate_levels'] != m.gate_levels:
        bad.append('header: gates per level %s, circuit has %s' % (t['gate_levels'], m.gate_levels))
    if 'and_levels' in t and t['and_levels'] != m.and_levels:
        bad.append('header: ANDs per level %s, circuit has %s' % (t['and_levels'], m.and_levels))
    return bad
