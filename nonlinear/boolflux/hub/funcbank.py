"""Function bank: every distinct signal truth table of the archived circuits with the cheapest known
gate level, AND level and cone AND count, the circuits it occurs in (up to 8), and interface tags
(N = x^17, N^-1, u = N + N^-1, affine combinations of the outputs).  DIR/funcbank/bank.json."""
from __future__ import annotations

import json
from pathlib import Path

from .common import core, interface_tags, atomic_write, ONES

MAX_OCC = 8


class FuncBank:
    def __init__(self, root):
        self.dir = Path(root) / 'funcbank'; self.dir.mkdir(parents=True, exist_ok=True)
        self.f = self.dir / 'bank.json'
        self.bank = json.loads(self.f.read_text()) if self.f.exists() else {}
        self.dirty = 0

    def add_circuit(self, c, ident):
        n = c.n; tabs = c.tables()
        gl = [0] * n; al = [0] * n; cone = [0] * n          # cone: bitset of AND gate indices
        new = 0
        for j, (op, a, b) in enumerate(c.gates):
            isand = op in core.NONLINEAR_OPS
            gl.append(1 + max(gl[a], gl[b])); al.append(max(al[a], al[b]) + (1 if isand else 0))
            cone.append(cone[a] | cone[b] | ((1 << j) if isand else 0))
        for s in range(n, n + len(c.gates)):
            t = tabs[s]
            if t in (0, ONES): continue
            k = '%064x' % t
            e = self.bank.get(k)
            ca = bin(cone[s]).count('1')
            if e is None:
                e = self.bank[k] = {'gl': gl[s], 'al': al[s], 'cone_and': ca, 'occ': [], 'tags': interface_tags(t)}
                new += 1
            else:
                e['gl'] = min(e['gl'], gl[s]); e['al'] = min(e['al'], al[s]); e['cone_and'] = min(e['cone_and'], ca)
            if ident not in e['occ'] and len(e['occ']) < MAX_OCC: e['occ'].append(ident)
        self.dirty += 1
        return new

    def save(self):
        atomic_write(self.f, json.dumps(self.bank))
        self.dirty = 0

    def tagged(self, tag):
        return {k: e for k, e in self.bank.items() if tag in e['tags']}
