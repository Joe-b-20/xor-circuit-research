"""Direct construction and linear-algebra checks of named continuation examples.

No search, enumeration of subspaces, optimization, or case elimination.
Affine intersections are solved by Gaussian elimination on the specified target span.
"""
from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO
import json
import runpy
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "research/structure-2026-11-11/compose/compat"))
import clib


def basis(vectors):
    pivots = {}
    for vector in vectors:
        while vector:
            bit = vector.bit_length() - 1
            if bit in pivots:
                vector ^= pivots[bit]
            else:
                pivots[bit] = vector
                break
    return pivots


def residue(vector, pivots):
    for bit in sorted(pivots, reverse=True):
        if vector >> bit & 1:
            vector ^= pivots[bit]
    return vector


def affine_intersection(reference, target_basis, window_mask):
    """Return a local representative and kernel basis, or None; no vector enumeration."""
    pivots = {}
    kernels = []
    for vector in target_basis:
        outside, lift = vector & ~window_mask, vector
        while outside:
            bit = outside.bit_length() - 1
            if bit in pivots:
                p, v = pivots[bit]
                outside ^= p
                lift ^= v
            else:
                pivots[bit] = (outside, lift)
                break
        if not outside:
            kernels.append(lift)
    outside, correction = reference & ~window_mask, 0
    while outside:
        bit = outside.bit_length() - 1
        if bit not in pivots:
            return None
        p, lift = pivots[bit]
        outside ^= p
        correction ^= lift
    representative = reference ^ correction
    assert representative & ~window_mask == 0
    assert all(k & ~window_mask == 0 for k in kernels)
    return representative, list(basis(kernels).values())


class Circuit:
    def __init__(self, n, blocks):
        self.n = n
        self.blocks = blocks
        self.values = [1 << i for i in range(n)]
        self.parents = [None] * n
        self.lookup = {v: i for i, v in enumerate(self.values)}
        self.outputs = []

    def add(self, a, b):
        value = self.values[a] ^ self.values[b]
        assert value
        if value in self.lookup:
            return self.lookup[value]
        node = len(self.values)
        self.lookup[value] = node
        self.values.append(value)
        self.parents.append((a, b))
        return node

    def chain(self, inputs):
        node = inputs[0]
        for other in inputs[1:]:
            node = self.add(node, other)
        return node

    def event(self, node):
        if node < self.n:
            return False
        a, b = self.parents[node]
        return any(self.values[a] & m and self.values[a] & m == self.values[b] & m
                   for m in self.blocks)

    def support_mask(self, value):
        return sum(m for m in self.blocks if value & m)

    def reach(self, stop_at_events=False):
        seen, pending = set(), self.outputs[:]
        while pending:
            v = pending.pop()
            if v in seen:
                continue
            seen.add(v)
            if self.parents[v] and not (stop_at_events and self.event(v)):
                pending.extend(self.parents[v])
        return seen


def completion_components(circuit, selected):
    windows = sorted({circuit.support_mask(circuit.values[o]) for o in circuit.outputs})
    # Include uncovered input blocks, as required by the theorem's convention.
    covered = 0
    for w in windows:
        covered |= w
    windows += [b for b in circuit.blocks if b & covered == 0]
    local = lambda value: any(value & ~w == 0 for w in windows)
    nodes = set()
    adjacency = {}
    endpoints = {}
    for f in selected:
        assert local(circuit.values[f])
        nonlocal_nodes = [a for a in circuit.parents[f] if not local(circuit.values[a])]
        assert nonlocal_nodes
        endpoints[f] = nonlocal_nodes
        nodes.update(nonlocal_nodes)
        for a in nonlocal_nodes:
            adjacency.setdefault(a, set())
        if len(nonlocal_nodes) == 2:
            a, b = nonlocal_nodes
            adjacency[a].add(b)
            adjacency[b].add(a)
    reports = []
    while nodes:
        component = set()
        todo = [min(nodes)]
        while todo:
            a = todo.pop()
            if a not in component:
                component.add(a)
                todo.extend(adjacency[a] - component)
        nodes -= component
        events = [f for f in selected if endpoints[f][0] in component]
        kb = basis(circuit.values[f] for f in events)
        reference = circuit.values[min(component)]
        assert all(residue(circuit.values[a] ^ reference, kb) == 0 for a in component)
        intersections = [r for w in windows
                         if (r := affine_intersection(reference, list(kb.values()), w)) is not None]
        report = {"hidden_operands": len(component), "selected_events": len(events),
                  "target_rank": len(kb), "eligible_windows": len(intersections)}
        no_mixed = all(len(endpoints[f]) == 2 for f in events)
        if intersections:
            anchor = intersections[0][0]
            differences = [v for rep, ker in intersections for v in [rep ^ anchor] + ker]
            db = basis(differences)
            assert all(residue(v, kb) == 0 for v in db.values())
            affine_rows = [(residue(circuit.values[f], db) << 1) | (len(endpoints[f]) == 1)
                           for f in events]
            bound = len(kb) - len(db)
            lifted = len(basis(affine_rows))
            assert bound <= lifted <= bound + 1 <= len(component) + 1
            assert lifted <= len(component)
            report.update(completion_difference_rank=len(db), AC=bound, AC_plus=lifted)
        else:
            assert no_mixed and len(component) >= len(kb) + 1
            report.update(AC0=len(kb) + 1)
        if no_mixed:
            assert len(component) >= len(kb) + 1
            report["actual_no_local_partner_bound"] = len(kb) + 1
        reports.append(report)
    return reports


def hub():
    # One fixed instance: r=3, m=3.
    r, m = 3, 3
    n = 2 + 2 * r * m
    z = [[2 + m * i + k for k in range(m)] for i in range(r)]
    w = [[2 + r * m + m * i + k for k in range(m)] for i in range(r)]
    blocks = [1, 2] + [sum(1 << j for j in zi) for zi in z]
    blocks += [1 << j for wi in w for j in wi]
    c = Circuit(n, blocks)
    a = c.add(0, 1)
    selected = []
    for i in range(r):
        p = 1
        for k in range(m):
            p = c.add(p, z[i][k])
            c.outputs.append(c.add(p, w[i][k]))
        selected.append(c.add(a, p))
        c.outputs.append(selected[-1])
    assert len(c.values) - n == 22
    assert c.reach() - c.reach(True) - set(range(n)) == {a}
    assert {v for v in range(n, len(c.values)) if c.event(v)} == set(selected)
    assert c.reach() >= set(range(n, len(c.values)))
    reports = completion_components(c, selected)
    assert len(reports) == 1 and reports[0]["completion_difference_rank"] == 2
    assert reports[0]["AC"] == reports[0]["AC_plus"] == 1

    clean = Circuit(n, blocks)
    for i in range(r):
        q = z[i][0]
        for k in range(m):
            if k:
                q = clean.add(q, z[i][k])
            p = clean.add(1, q)
            clean.outputs.append(clean.add(p, w[i][k]))
        clean.outputs.append(clean.add(0, q))
    assert [clean.values[v] for v in clean.outputs] == [c.values[v] for v in c.outputs]
    assert len(clean.values) - n == 27
    assert not any(clean.event(v) for v in range(n, len(clean.values)))
    return {"r": r, "m": m, "gates": 22, "hidden": 1, "events": 3,
            "event_free_construction_gates": 27, "event_free_optimality": "hand proof in MULTIWINDOW.md",
            "components": reports}


def block_target(sheet, row):
    # Convert the independent AES-polynomial matrix to block-major wire order.
    original = clib.ROWS[(row, sheet)]
    return sum(((original >> (8 * c + d)) & 1) << (4 * d + c)
               for c in range(4) for d in range(8))


def actual_overlap():
    with redirect_stdout(StringIO()):
        data = runpy.run_path(str(HERE / "check_overlap.py"))
    c = Circuit(32, [15 << (4 * d) for d in range(8)])
    c.values = data["reduced_values"]
    c.parents = data["reduced_parents"]
    c.outputs = list(data["outputs"].values())
    assert all(c.values[o] == block_target(*key) for key, o in data["outputs"].items())
    selected = [data["outputs"][3, 0], data["outputs"][4, 0]]
    reports = completion_components(c, selected)
    assert reports[0]["target_rank"] == reports[0]["completion_difference_rank"] == 2
    assert reports[0]["AC"] == 0 and reports[0]["AC_plus"] == 1
    return {"live_gates": len(c.reach() - set(range(32))), "hidden": len(c.reach() - c.reach(True) - set(range(32))),
            "components": reports}


def internal_no_hidden():
    c = Circuit(32, [15 << (4 * d) for d in range(8)])
    x = [8 + i for i in range(4)]
    z = [4 + i for i in range(4)]
    u = c.add(z[0], z[1])
    a, b = c.add(u, x[1]), c.add(u, x[2])
    f = c.add(a, b)
    out = {}
    out[2, 0] = c.add(c.add(a, x[2]), x[3])
    out[2, 1] = c.add(c.add(b, c.add(z[0], z[2])), c.add(x[0], x[3]))
    out[2, 2] = c.add(c.add(c.add(c.add(z[2], z[3]), x[0]), x[1]), x[3])
    out[2, 3] = c.add(c.add(f, x[0]), c.add(z[3], z[0]))
    for sheet in range(8):
        for row in range(4):
            if (sheet, row) in out:
                continue
            wanted = block_target(sheet, row)
            inputs = [j for j in range(32) if wanted >> j & 1]
            if (sheet, row) == (3, 1):
                first = next(j for j in inputs if j // 4 == 3)
                inputs = [first] + [j for j in inputs if j != first]
            out[sheet, row] = c.chain(inputs)
    c.outputs = list(out.values())
    assert all(c.values[o] == block_target(*key) for key, o in out.items())
    assert len(set(c.values)) == len(c.values)
    live = c.reach() - set(range(32))
    assert live == set(range(32, len(c.values)))
    assert {v for v in live if c.event(v)} == {f}
    assert c.reach() - c.reach(True) - set(range(32)) == set()
    assert f not in c.outputs
    return {"live_gates": len(live), "hidden": 0, "events": 1,
            "event_internal": True, "all_32_masks_correct": True, "reduced": True}


def internal_tree():
    # The one specified four-vertex star from INTERNAL.md's AC0 sharpness family.
    c = Circuit(6, [15, 16, 32])
    hidden = [c.add(4, i) for i in range(4)]
    selected = [c.add(hidden[0], hidden[i]) for i in (1, 2, 3)]
    c.outputs = [c.add(f, 5) for f in selected] + [4]
    assert c.reach() - c.reach(True) - set(range(6)) == set(hidden)
    reports = completion_components(c, selected)
    assert reports[0]["eligible_windows"] == 0
    assert reports[0]["AC0"] == reports[0]["hidden_operands"] == 4
    return {"gates": len(c.values) - 6, "hidden": 4, "internal_events": 3,
            "components": reports}


def sparse_packed():
    # One fixed instance: r=2, packed private blocks of dimensions 4,3,2.
    r = 2
    z = [[4 + 3 * i + k for k in range(3)] for i in range(r)]
    cursor = 4 + 3 * r
    w = []
    for i in range(r):
        group = []
        for k in range(1, 4):
            group.append(list(range(cursor, cursor + 5 - k)))
            cursor += 5 - k
        w.append(group)
    n = cursor
    blocks = [3, 12] + [sum(1 << j for j in zi) for zi in z]
    blocks += [sum(1 << j for j in wij) for wi in w for wij in wi]
    assert n == 28 and max(b.bit_count() for b in blocks) == 4
    c = Circuit(n, blocks)
    xp, yp = c.add(0, 1), c.add(2, 3)
    a = c.add(xp, yp)
    selected = []
    for i in range(r):
        p = yp
        for k in range(3):
            p = c.add(p, z[i][k])
            out = p
            for private in w[i][k]:
                out = c.add(out, private)
            c.outputs.append(out)
        selected.append(c.add(a, p))
        c.outputs.append(selected[-1])
    assert len(c.values) - n == 29
    assert c.reach() - c.reach(True) - set(range(n)) == {xp, a}
    assert {v for v in range(n, len(c.values)) if c.event(v)} == set(selected)
    assert c.reach() >= set(range(n, len(c.values)))
    assert sorted(c.values[o].bit_count() for o in c.outputs) == [5, 5] + [7] * 6
    assert len(basis(c.values[o] for o in c.outputs)) == 8
    assert max(sum(bool(c.values[o] & b) for b in blocks) for o in c.outputs) == 3
    reports = completion_components(c, selected)
    assert reports[0]["AC"] == reports[0]["AC_plus"] == 1

    clean = Circuit(n, blocks)
    xp, yp = clean.add(0, 1), clean.add(2, 3)
    for i in range(r):
        q = z[i][0]
        for k in range(3):
            if k:
                q = clean.add(q, z[i][k])
            p = clean.add(yp, q)
            out = p
            for private in w[i][k]:
                out = clean.add(out, private)
            clean.outputs.append(out)
        clean.outputs.append(clean.add(xp, q))
    assert len(clean.values) - n == 32
    assert not any(clean.event(v) for v in range(n, len(clean.values)))
    assert [clean.values[o] for o in clean.outputs] == [c.values[o] for o in c.outputs]
    return {"r": r, "inputs": n, "outputs": len(c.outputs), "output_rank": 8,
            "gates": 29, "hidden_gates": 2, "nonlocal_operands": 1,
            "visible_events": 2, "max_block_dimension": 4, "max_window_blocks": 3,
            "output_weights": [5, 7], "event_free_construction_gates": 32,
            "event_free_optimum": "15r+2 by hand proof in SPARSE.md",
            "boundary_relation_minimum": "6 by hand proof in SPARSE.md; not enumerated",
            "components": reports}


if __name__ == "__main__":
    results = {"hub_r3_m3": hub(), "mixcolumns_overlap": actual_overlap(),
               "mixcolumns_internal_no_hidden": internal_no_hidden(),
               "internal_tree_h4": internal_tree(), "sparse_packed_r2": sparse_packed()}
    (HERE / "check-results.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))
