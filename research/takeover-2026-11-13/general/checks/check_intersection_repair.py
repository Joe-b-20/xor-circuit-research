#!/usr/bin/env python3
"""Direct verification of fixed forest quotients and repair constructions.

No circuit search, representation enumeration, or parameter optimization.
"""

import json

from check_joint_supply import coordinate_circuit, rank


def xor_values(values):
    result = 0
    for value in values:
        result ^= value
    return result


def pair_certificate(circ, roots):
    assert len(roots) == 2
    n = circ.initial_count
    retained = set(roots)
    for gate in reversed(range(len(circ.gates))):
        result = n + gate
        if result in retained:
            retained.update(circ.gates[gate])
    readers = {i: [] for i in retained}
    neighbors = {i: set() for i in retained}
    for gate, parents in enumerate(circ.gates):
        result = n + gate
        if result in retained:
            for parent in parents:
                readers[parent].append(result)  # operand ports, not a set
                neighbors[parent].add(result)
                neighbors[result].add(parent)
    components = 0
    unseen = set(retained)
    while unseen:
        components += 1
        stack = [unseen.pop()]
        while stack:
            for other in neighbors[stack.pop()]:
                if other in unseen:
                    unseen.remove(other)
                    stack.append(other)
    ports = {i: [] for i in retained}
    for bit, root in enumerate(roots):
        ports[root].append(1 << bit)
    eta = {}
    for node in sorted(retained, reverse=True):
        eta[node] = xor_values([eta[r] for r in readers[node]] + ports[node])
    phi = lambda value: int(value == 3)
    chosen = []
    branch_count = 0
    excess = 0
    for node in sorted(retained):
        degree = len(readers[node]) + len(ports[node])
        assert degree >= 1
        excess += degree - 1
        branch_count += degree >= 2
        defect = phi(eta[node]) ^ xor_values(phi(eta[r]) for r in readers[node])
        defect ^= xor_values(phi(port) for port in ports[node])
        if defect:
            assert degree >= 2
            chosen.append(node)
    a = sum(node < n for node in retained)
    g = len(retained) - a
    beta = g - a + components
    intersection = circ.values[roots[0]] & circ.values[roots[1]]
    assert xor_values(circ.values[node] for node in chosen) == intersection
    assert branch_count <= excess == beta + 2 - components
    assert len(chosen) <= beta + 1
    return dict(ancestor_inputs=a, ancestor_gates=g, components=components,
                full_cycle_rank=beta, branch_count=branch_count,
                certificate_terms=len(chosen), intersection=intersection)


def forest_quotient(circ):
    n = circ.initial_count
    parent = list(range(len(circ.values)))

    def root(i):
        while i != parent[i]:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    cuts = {}
    cut_sources = []
    for gate, operands in enumerate(circ.gates):
        result = n + gate
        for port, source in enumerate(operands):
            left, right = root(source), root(result)
            if left == right:
                cuts[(gate, port)] = len(cut_sources)
                cut_sources.append(source)
            else:
                parent[left] = right
    c = len({root(i) for i in range(len(circ.values))})
    beta = len(circ.gates) - n + c
    assert len(cut_sources) == beta
    formal = [1 << i for i in range(n)]
    for gate, operands in enumerate(circ.gates):
        values = []
        for port, source in enumerate(operands):
            values.append(1 << (n + cuts[(gate, port)])
                          if (gate, port) in cuts else formal[source])
        formal.append(values[0] ^ values[1])
    columns = [1 << i for i in range(n)] + [circ.values[s] for s in cut_sources]

    def project(mask):
        return xor_values(columns[i] for i in range(len(columns)) if mask & (1 << i))

    assert [project(mask) for mask in formal] == circ.values
    relations = []
    for j, source in enumerate(cut_sources):
        assert formal[source] >> (n + j) == 0  # only earlier shadow inputs
        relation = (1 << (n + j)) ^ formal[source]
        assert project(relation) == 0
        relations.append(relation)
    assert rank(relations) == beta
    assert rank(columns) == n
    assert len(circ.gates) - (n + beta) + c == 0
    return dict(shadows=beta, kernel_rank=rank(relations),
                all_gate_projections_verified=True, causal_relations_verified=True)


def one_cycle_family():
    m = 4
    n = 2*m + 2
    r, z = 0, n-1
    a = [1 + 2*i for i in range(m)]
    b = [2 + 2*i for i in range(m)]
    circ = coordinate_circuit(n)
    pairs = [circ.add(ai, bi) for ai, bi in zip(a, b)]
    current = r
    prefixes = []
    for pair in pairs:
        current = circ.add(current, pair)
        prefixes.append(current)
    q = circ.add(current, circ.add(r, z))
    cumulative = []
    mask = 0
    for pair in pairs:
        mask ^= circ.values[pair]
        cumulative.append(mask)
    assert [circ.values[p] & circ.values[q] for p in prefixes] == cumulative
    missing = cumulative[1:]
    assert all(value not in circ.values for value in missing)
    assert rank(missing) == m-1
    outputs = [r] + b + prefixes + [q]
    rows = [circ.values[i] for i in outputs]
    assert rank(rows) == n
    # Verify the displayed inverse using ordinary input-coordinate masks.
    previous = circ.values[r]
    for ai, bi, prefix in zip(a, b, prefixes):
        assert circ.values[prefix] ^ previous ^ circ.values[bi] == 1 << ai
        previous = circ.values[prefix]
    assert circ.values[q] ^ previous ^ circ.values[r] == 1 << z
    cert = pair_certificate(circ, [prefixes[2], q])
    assert cert['full_cycle_rank'] == 1 and cert['certificate_terms'] == 2
    stats = circ.stats(prefixes + [q])
    assert stats['gates'] == n and stats['odd_graph_cycles'] == 0
    assert stats['even_plus_even'] == 0
    repaired = coordinate_circuit(n)
    pair_nodes = [repaired.add(ai, bi) for ai, bi in zip(a, b)]
    sums = [pair_nodes[0]]
    for pair in pair_nodes[1:]:
        sums.append(repaired.add(sums[-1], pair))
    repaired_prefixes = [repaired.add(r, value) for value in sums]
    repaired_q = repaired.add(sums[-1], z)
    assert [repaired.values[i] for i in sums] == cumulative
    assert [repaired.values[i] for i in repaired_prefixes] == [circ.values[i] for i in prefixes]
    assert repaired.values[repaired_q] == circ.values[q]
    assert len(repaired.gates) == 3*m
    return dict(parameter=m, inputs=n, original_gates=len(circ.gates),
                repaired_gates=len(repaired.gates), proved_repair_penalty=m-2,
                missing_intersection_rank=rank(missing), square_map_rank=rank(rows),
                parity_odd_graph_cycles=stats['odd_graph_cycles'],
                pair_certificate=cert, forest_quotient=forest_quotient(circ))


def sharp_optimal_family():
    t = 3
    core_n = 3*t + 2
    even_count = 4*t - 2
    n = core_n + even_count
    circ = coordinate_circuit(n)
    c = list(range(t))
    a = list(range(t, 2*t))
    b = list(range(2*t, 3*t))
    x, y = 3*t, 3*t+1
    aa = [circ.add(ci, ai) for ci, ai in zip(c, a)]
    bb = [circ.add(ci, bi) for ci, bi in zip(c, b)]
    av, bv = aa[0], bb[0]
    for node in aa[1:]:
        av = circ.add(av, node)
    for node in bb[1:]:
        bv = circ.add(bv, node)
    evens = list(range(n, len(circ.values)))
    assert len(evens) == even_count
    u, v = circ.add(x, av), circ.add(y, bv)
    tagged = [circ.add(h, core_n+i) for i, h in enumerate(evens)]
    rows = [1 << i for i in range(3*t)] + [circ.values[u], circ.values[v]]
    rows += [circ.values[i] for i in tagged]
    assert len(rows) == n == 7*t
    assert all(row.bit_count() % 2 == 1 for row in rows)
    assert rank(rows) == n
    for i, row in enumerate(rows):
        assert xor_values(rows[j] for j in range(n) if row & (1 << j)) == 1 << i
    quotient_columns = [1 << (i % t) for i in range(3*t)] + [0]*(n-3*t)

    def block_image(value):
        return xor_values(quotient_columns[i] for i in range(n) if value & (1 << i))

    assert all(block_image(value) == 0 for value in circ.values[n:])
    intersection = circ.values[u] & circ.values[v]
    assert block_image(intersection) == (1 << t)-1
    assert intersection == xor_values(1 << i for i in c)
    cert = pair_certificate(circ, [u, v])
    assert cert['full_cycle_rank'] == t-1
    assert cert['certificate_terms'] == t
    assert len(circ.gates) == 8*t-2
    quotient = forest_quotient(circ)
    assert quotient['shadows'] == t-1
    return dict(parameter=t, inputs=n, gates=len(circ.gates),
                proved_dictionary_length=t, square_map_rank=rank(rows),
                involution_verified=True, quotient_lower_certificate_verified=True,
                pair_certificate=cert, forest_quotient=quotient)


if __name__ == '__main__':
    print(json.dumps(dict(one_cycle=one_cycle_family(),
                         sharp_optimal=sharp_optimal_family(),
                         circuit_search=False, representation_search=False), indent=2))
