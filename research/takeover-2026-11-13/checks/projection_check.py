"""Direct construction verification only; no search or parameter-family elimination.

Builds the two repairs of PROJECTION.md on individually specified examples.
Every check compares exact linear masks, so it covers all input assignments.
Run from anywhere with Python 3; standard library only. Optional external corpus
examples are read once at their named line and copied into local fixtures.
"""
from pathlib import Path
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = ROOT / "research/structure-2026-11-11"
sys.path.insert(0, str(OLD / "compose/compat"))
import clib  # inspected read-only circuit loader; no main executes


def values(n, gates):
    ans = [1 << i for i in range(n)]
    for a, b in gates:
        assert 0 <= a < len(ans) and 0 <= b < len(ans)
        ans.append(ans[a] ^ ans[b])
    return ans


def repair(n, gates, targets, block_masks):
    original = values(n, gates)
    assert all(t and t in original for t in targets)
    assert sum(block_masks) == (1 << n) - 1
    assert sum(m.bit_count() for m in block_masks) == n

    def support(val):
        return sum(1 << d for d, mask in enumerate(block_masks) if val & mask)

    def project(val, request):
        return val & sum(mask for d, mask in enumerate(block_masks) if request >> d & 1)

    supports = [support(v) for v in original]
    requests = [set() for _ in original]
    output_nodes = [original.index(t) for t in targets]
    for node in output_nodes:
        requests[node].add(supports[node])
    for node in range(len(original) - 1, n - 1, -1):
        for request in requests[node]:
            assert request and request & supports[node] == request
            for operand in gates[node - n]:
                child = request & supports[operand]
                if child:
                    requests[operand].add(child)

    # Construct both the physical-request lift and the value-identified lift.
    q = []
    new_gates = []
    new_vals = original[:n]
    index = {v: i for i, v in enumerate(new_vals)}
    projected_values = {project(original[v], s) for v in range(len(original)) for s in requests[v]}
    projected_values -= set(original[:n])
    assert 0 not in projected_values
    for node, (a, b) in enumerate(gates, n):
        productive = 0
        for request in sorted(requests[node]):
            va = project(original[a], request)
            vb = project(original[b], request)
            out = project(original[node], request)
            assert va ^ vb == out and out
            if va:
                assert va in index
            if vb:
                assert vb in index
            if va and vb:
                productive += 1
                assert not any(va & mask and va & mask == vb & mask for mask in block_masks)
            if out not in index:
                assert va and vb
                new_gates.append((index[va], index[vb]))
                index[out] = len(new_vals)
                new_vals.append(out)
        q.append(productive)

    assert set(new_vals[n:]) == projected_values
    assert len(new_gates) == len(projected_values) <= sum(q)
    assert values(n, new_gates) == new_vals
    assert all(t in index for t in targets)
    for a, b in new_gates:
        assert not any(new_vals[a] & mask and new_vals[a] & mask == new_vals[b] & mask
                       for mask in block_masks)

    live = set()
    stack = [index[t] for t in targets]
    while stack:
        node = stack.pop()
        if node < n or node in live:
            continue
        live.add(node)
        stack.extend(new_gates[node - n])

    old_set = set(original[n:])
    added = len(projected_values - old_set)
    deleted = len(old_set - projected_values)
    duplicate_count = len(gates) - len(old_set)
    assert len(projected_values) == len(gates) - duplicate_count - deleted + added
    X = sum(max(k - 1, 0) for k in q)
    Z = q.count(0)
    assert sum(q) == len(gates) - Z + X
    return {"gates": len(gates), "productive_requests": sum(q), "X": X, "Z": Z,
            "distinct_projected_gates": len(projected_values), "added_values": added,
            "removed_values": deleted, "pruned_repair_gates": len(live),
            "reduced": len(set(original)) == len(original) and 0 not in original,
            "computes_targets": True, "repair_event_free": True}


def prefix(n, extra_clean_outputs=False):
    inputs = n + 1
    gates = []
    p = 0
    for i in range(1, n + 1):
        gates.append((p, i))
        p = inputs + len(gates) - 1
    if extra_clean_outputs:
        acc = 1
        for i in range(2, n):
            gates.append((acc, i))
            acc = inputs + len(gates) - 1
    gates.append((p, 0))
    return inputs, gates, values(inputs, gates)[inputs:], [1 << i for i in range(inputs)]


def main():
    results = {}
    # These parameters are fixed named examples, not a sweep or least-gate search.
    for name, case in [("prefix_n5", prefix(5)),
                       ("prefix_n5_with_clean_outputs", prefix(5, True))]:
        results[name] = repair(*case)
    assert results["prefix_n5"]["distinct_projected_gates"] == 9
    assert results["prefix_n5_with_clean_outputs"]["distinct_projected_gates"] == 9
    assert results["prefix_n5_with_clean_outputs"]["productive_requests"] == 12

    five_targets = [3, 7, 15, 14, 12]
    original_five = [(0, 1), (4, 2), (5, 3), (6, 0), (7, 1)]
    clean_five = [(0, 1), (2, 3), (4, 2), (1, 5), (4, 5)]
    results["five_output_no_converse"] = repair(4, original_five, five_targets, [1, 2, 4, 8])
    results["five_output_event_free_optimum"] = repair(4, clean_five, five_targets, [1, 2, 4, 8])
    assert results["five_output_no_converse"]["distinct_projected_gates"] == 6
    assert results["five_output_event_free_optimum"]["distinct_projected_gates"] == 5

    blocks = [clib.bm(j) for j in range(8)]
    targets = list(clib.ROWS.values())
    # Matrix independently represented by repository bit matrix must agree with AES multiplication.
    assert clib.rlib.mc_model()["rows"] == clib.ROWS
    results["mixcolumns_r88"] = repair(32, clib.load("r88"), targets, blocks)

    fixtures = HERE / "fixtures"
    fixtures.mkdir(exist_ok=True)
    for source in ["circuits_2.txt:783", "circuits_3.txt:1451", "circuits_3.txt:3001"]:
        fixture = fixtures / (source.replace(":", "_line_") + ".json")
        if fixture.exists():
            gates = json.loads(fixture.read_text())
        else:
            gates = clib.load(source)
            fixture.write_text(json.dumps(gates) + "\n")
        results[source] = repair(32, gates, targets, blocks)

    qn, qg = clib.rlib.read_qm(OLD / "rotation/circuits/q3_28.txt")
    qt = list(clib.rlib.qm_model(3)["rows"].values())
    results["Q3_28"] = repair(qn, qg, qt, [15 << (4 * j) for j in range(3)])

    spec = importlib.util.spec_from_file_location("specified_witness", OLD / "cancel/witness/build_witness.py")
    witness = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(witness)
    assert witness.mc_rows() == clib.ROWS
    wg = witness.build(32, lambda w: w // 8, lambda w: w % 8, clib.ROWS, 8,
                       lambda w: (w % 8, w // 8))
    results["superposition_block_order"] = repair(32, wg, targets, blocks)
    assert witness.stats(32, wg, clib.ROWS, clib.bm, 8)["distinct_charged"] == 66

    # Unreduced/zero internal nodes and partial within-block cancellation controls.
    results["unreduced_zero_internal"] = repair(2, [(0, 0), (0, 1), (2, 3)], [3], [1, 2])
    results["within_block_partial"] = repair(3, [(0, 1), (1, 2), (3, 4)], [5], [7])
    out = HERE / "projection-results.json"
    out.write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
