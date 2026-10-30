"""Exact scalar certificate for PROOF72.md; Python standard library only."""
import json
from math import comb
from pathlib import Path


def g(s):
    """Maximum z + binomial(q, 2) subject to q + z = s."""
    assert s >= 0
    result = max(s, comb(s, 2))
    assert result == max(s - q + comb(q, 2) for q in range(s + 1))
    return result


def minimum_s(x, gate_count=71):
    """Use only y >= 0 in the universal incidence inequality."""
    target = 96 - 2 * gate_count + 2 * x
    return next(s for s in range(2 * gate_count + 1) if g(s) >= target)


def check():
    rows = []
    for a in range(24, 27):
        t = 39 - a
        b_maximum = 26 + (3 * t - 32) // 2
        for b in range(24, b_maximum + 1):
            increment = minimum_s(a) + minimum_s(b) + 50 - a - b
            assert increment > 0
            rows.append({"a": a, "b": b,
                         "minimum_s_a": minimum_s(a),
                         "minimum_s_b": minimum_s(b),
                         "two_step_increment": increment})
    assert len(rows) == 23
    assert min(row["two_step_increment"] for row in rows) == 3
    # The same proof excludes 69 and 70 directly, removing any dependence
    # on the larger label-capacity certificates used in the prior 71 bound.
    complete = []
    for gates in range(69, 72):
        pairs = []
        for a in range(24, gates-44):
            t = gates-32-a
            b_maximum = gates-45+(3*t-32)//2
            for b in range(24, b_maximum+1):
                increment = (minimum_s(a, gates)+minimum_s(b, gates)
                             +192-2*gates-a-b)
                assert increment > 0
                pairs.append({"a":a,"b":b,"increment":increment})
        complete.append({"gates":gates,"pair_count":len(pairs),
                         "minimum_increment":min(p['increment'] for p in pairs),
                         "pairs":pairs})
    return {"gate_count_excluded": 71, "pair_count": len(rows),
            "minimum_two_step_increment": 3, "pairs": rows,
            "direct_69_through_71_exclusion":complete}


if __name__ == "__main__":
    report = check()
    Path(__file__).with_name("CHECK72.json").write_text(
        json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
