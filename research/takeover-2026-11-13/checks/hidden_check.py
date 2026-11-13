"""Verify one specified sharp construction for Theorem H by exact linear algebra.

The construction is the four-vertex star, not a search over trees or circuits.
The symbolic proof, valid for any tree, is in directions/independent.md.
"""
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent


def rank(vectors):
    basis = {}
    for vector in vectors:
        while vector:
            pivot = vector.bit_length() - 1
            if pivot in basis:
                vector ^= basis[pivot]
            else:
                basis[pivot] = vector
                break
    return len(basis)


def main():
    h = 4
    edges = [(0, 1), (0, 2), (0, 3)]
    n = 3 * h + 1
    q = 3 * h
    vals = [1 << i for i in range(n)]
    gates = []

    def add(a, b):
        gates.append((a, b))
        vals.append(vals[a] ^ vals[b])
        return len(vals) - 1

    local_l = [add(q, h + i) for i in range(h)]
    local_b = [add(q, 2 * h + i) for i in range(h)]
    hidden = [add(local_l[i], i) for i in range(h)]
    targets = [add(hidden[i], local_b[i]) for i in range(h)]
    targets += [add(hidden[i], hidden[j]) for i, j in edges]
    outputs = local_l + local_b + targets
    blocks = [(1 << h) - 1, ((1 << (2 * h)) - 1) << h, 1 << q]

    def support(v):
        return frozenset(i for i, b in enumerate(blocks) if v & b)

    windows = {support(vals[o]) for o in outputs}
    assert windows == {frozenset({0, 1}), frozenset({1, 2})}
    # {0,1} is a maximal clique because the only outside block 2 misses block 0.
    assert all(not {0, 2} <= w for w in windows)
    nonlocal_nodes = {i for i in range(n, len(vals)) if not any(support(vals[i]) <= w for w in windows)}
    assert nonlocal_nodes == set(hidden)
    events = {n + i for i, (a, b) in enumerate(gates)
              if any(vals[a] & block and vals[a] & block == vals[b] & block for block in blocks)}
    assert events == set(targets)
    assert len(set(vals)) == len(vals) and 0 not in vals
    assert rank([vals[o] for o in targets]) == len(targets)
    for block in blocks[:2]:
        assert len({vals[o] & block for o in targets}) == len(targets)
    assert len(targets) == 2 * len(hidden) - 1

    # Trace backwards through non-events: exactly the named local outputs are retained.
    retained = set()
    visible = set()
    stack = outputs[:]
    while stack:
        node = stack.pop()
        if node < n:
            continue
        if node in events:
            visible.add(node)
        elif node not in retained:
            retained.add(node)
            stack.extend(gates[node - n])
    assert visible == events and retained == set(local_l + local_b)
    assert set(range(n, len(vals))) - visible - retained == set(hidden)
    result = {"construction": "four-vertex star", "gates": len(gates),
              "selected_events": len(targets), "event_value_rank": rank([vals[o] for o in targets]),
              "hidden_gates": len(hidden), "hidden_operand_components": 1,
              "theorem_H_equality": True, "reduced": True, "verified": True}
    (HERE / "hidden-results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
