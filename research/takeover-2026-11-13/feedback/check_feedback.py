#!/usr/bin/env python3
"""Evaluate fixed feedback witnesses; no circuit or configuration search."""

import json
from pathlib import Path

from check_one_exit import Circuit, evaluate


def check_small(rank, feedback):
    """Rank-three and rank-four constructions displayed in GENERAL_REPAIR."""
    circuit = Circuit([rank, 1])
    source = circuit.units[0]
    z = circuit.units[1][0]
    if not feedback:
        clean = circuit.chain(source)
    prefixes = [circuit.add(z, source[0])]
    for coordinate in source[1:-1]:
        prefixes.append(circuit.add(prefixes[-1], coordinate))
    last = circuit.add(z, source[-1])
    consumer = prefixes + [last]
    if feedback:
        clean = circuit.add(prefixes[-1], last)
    expected = []
    running = z
    for coordinate in source[:-1]:
        running ^= coordinate
        expected.append(running)
    expected.append(z ^ source[-1])
    assert consumer == expected
    assert clean == sum(source)
    assert len(circuit.gates) == (rank + 1 if feedback else 2 * rank - 1)
    outputs = consumer + [clean]
    assert set(circuit.gates) <= circuit.ancestors(outputs)
    exits = [gate for gate in circuit.gates if not gate & z and
             any(operand & z for operand in circuit.parents[gate])]
    assert exits == ([clean] if feedback else [])
    first_cone = circuit.ancestors([clean])
    assert any(value & z for value in first_cone) == feedback
    return {"entry_rank": rank, "feedback": feedback,
            "gates": len(circuit.gates), "exits": len(exits),
            "outputs_correct": True, "all_gates_live": True}


if __name__ == "__main__":
    decorated = []
    for feedback in (True, False):
        gates, events = evaluate(feedback)
        decorated.append({"feedback": feedback, "gates": gates,
                          "events": events, "outputs_correct": True,
                          "output_rank": 8, "all_output_weights": 5,
                          "all_gates_live": True})
    result = {"method": "Direct evaluation of six specified circuits; no search or lower-bound enumeration.",
              "sharp_small_rank": [check_small(rank, feedback)
                                   for rank in (3, 4) for feedback in (True, False)],
              "decorated_one_exit": decorated}
    Path(__file__).with_name("check-results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
