#!/usr/bin/env python3
"""Independent check of CERTIFICATES_PKG75_G75.json (standard library only, exact integer arithmetic).

Independence from the generator: the rows are NOT taken from certify75.system (which the generator used) but written
here from the row list of lp_regen.rows_for (the lb76 transcription "from the proof documents"), re-typed below with
integer arithmetic; the scalar domain at G = 75 is enumerated here; no optimizer is used.
Checks:
 1. every certificate is a vector of nonnegative integers over the rows of its key (three equalities as <= and >=,
    then the inequalities in order) with nonnegative combination on every type column and weighted right side <= -1;
 2. the claims are exactly the domain {scalar states at G = 75} x {M, Mt}, each once;
 3. for every claim marked excluded: l_e <= k <= S_e + 1 (resp. l), every key below the stated k (even phase) and l (odd
    phase) that passes the incidence test and is not directly excluded has a certificate, and k > S_e or l > S_o or
    k + l > budget;
 4. the excluded set is disjoint from the published certified sets and from the open set, and its count is 5,908
    (optional, when the files are present).
"""
import json, sys
from math import comb
from pathlib import Path
HERE = Path(__file__).resolve().parent
G = 75
RHO6 = {"M": 20, "Mt": 28}; RESERVE = {"M": 8, "Mt": 4}


def rows(key):
    """(types, rows, bounds): rows as integer lists over types, every row meaning  row . n <= bound."""
    h, y, F, ori, q, z = key
    types = [(r, u, v) for r in range(4) for u in range(q + 1) for v in range(min(2 * z, max(0, h - 1)) + 1) if r + u + v >= 3]
    f = lambda r, u, v: max(0, (r + u + v - 3) // 2)
    deficit = lambda r, u: u - 1 if r == 0 else 0
    overflow = lambda r, u: max(0, u - 2) if r == 3 else 0
    rho = RHO6[ori]; res = RESERVE[ori]
    eq = [(lambda r, u, v: 1, h), (lambda r, u, v: r + u + v, 32 + h - y + q + z), (lambda r, u, v: v, 2 * z)]
    le = [
        (f, F),
        (lambda r, u, v: comb(u, 2), comb(q, 2)),
        (lambda r, u, v: u if r == 3 else 0, q),
        (lambda r, u, v: r * u, 7 * q),
        (lambda r, u, v: 1 + 2 * f(r, u, v) if r == 3 else 0, 3 * h + 2 * F + y - 32),
        (lambda r, u, v: max(0, r - 1) * u, 3 * q),
        (lambda r, u, v: u + 2 * f(r, u, v), 4 * q + 2 * F),
        (lambda r, u, v: u + v if r == 3 else 0, q + z),
        (lambda r, u, v: max(0, r - 1), rho),
        (lambda r, u, v: r * u - 2 * deficit(r, u), 2 * y + 2 * z + 7 * q - 2 * res),
        (lambda r, u, v: r * u + (u if r == 3 else 0) - 2 * deficit(r, u), 2 * y + 2 * z + 7 * q - 2 * res + (2 if ori == "M" else 0)),
        (lambda r, u, v: max(0, r - 1) * u - deficit(r, u), y + z + 3 * q - res),
        (lambda r, u, v: max(0, r - 1) * u + overflow(r, u), 3 * q),
    ]
    if ori == "M":
        le.append((lambda r, u, v: 2 * max(0, r - 1) * u + 2 * overflow(r, u) - 3 * deficit(r, u), 3 * y + 3 * z + 6 * q - 24))
    else:
        le += [(lambda r, u, v: max(0, r - 1) * u + overflow(r, u) - 3 * deficit(r, u), 3 * y + 3 * z + 3 * q - 12),
               (lambda r, u, v: r * u + (u if r == 3 else 0) - 3 * deficit(r, u), 3 * y + 3 * z + 7 * q - 12),
               (lambda r, u, v: -(u + v - 1) if r == 0 else (-v if r == 1 else 0), y - 3),
               (lambda r, u, v: -(3 * u + v - 3) if r == 0 else 0, 3 * y + 2 * z - 9)]
        if q == 0:
            le += [(lambda r, u, v: -int(r == 0), -1), (lambda r, u, v: -(v - 1) if r == 0 else 0, y - 3)]
    if q == 6: le.append((lambda r, u, v: {3: 1, 4: 3, 5: 4, 6: 4}.get(u, 0), 4))
    if q == 7: le.append((lambda r, u, v: {3: 2, 4: 7, 5: 12, 6: 14, 7: 14}.get(u, 0), 14))
    R = []; Bd = []
    for fn, b in eq:
        row = [fn(*t) for t in types]
        R.append(row); Bd.append(b); R.append([-c for c in row]); Bd.append(-b)
    for fn, b in le:
        R.append([fn(*t) for t in types]); Bd.append(b)
    return types, R, Bd


def direct(key):
    h, y, F, ori, q, z = key
    return (q == 0 and z == 0) or (ori == "Mt" and q == 0 and z < 8)


def scalar_states():
    def low(h, y): return next(s for s in range(65) if 2 * h + y + max(s, comb(s, 2)) >= 32)
    for a in range(24, G - 44):
        for Y in range(G - 31 - a):
            he = G - 32 - a - Y
            for b in range(24, G - 31):
                for V in range(Y + 1):
                    ho = G - 32 - b - V
                    if ho < 0 or ho + Y < 13: continue
                    Se = min(3 * he + 2 * V + Y - 32, 2 * b - a + G - 96 + V)
                    So = min(3 * ho + 2 * Y + V - 32, 2 * a - b + G - 96 + Y)
                    if min(Se, So) < 0: continue
                    le, lo = low(he, Y), low(ho, V); budget = a + b + 2 * G - 192
                    if le <= Se and lo <= So and le + lo <= budget:
                        yield (a, b, Y, V, he, ho, le, lo, Se, So, budget)


def main():
    data = json.load(open(sys.argv[1] if len(sys.argv) > 1 else HERE / "CERTIFICATES_PKG75_G75.json"))
    assert data["gates"] == G
    certs = {}; coeffs = 0; maxrhs = None
    for e in data["certificates"]:
        key = tuple(e["key"]); w = e["weights"]
        assert key not in certs
        types, R, Bd = rows(key)
        assert types, ("certificate for a key without columns", key)
        assert isinstance(w, list) and len(w) == len(R) and all(type(x) is int and x >= 0 for x in w), ("weights", key)
        rhs = sum(x * b for x, b in zip(w, Bd)); assert rhs <= -1, ("right side", key, rhs)
        for j in range(len(types)):
            assert sum(x * row[j] for x, row in zip(w, R)) >= 0, ("column", key, types[j])
        coeffs += len(types); maxrhs = rhs if maxrhs is None else max(maxrhs, rhs)
        certs[key] = True
    states = list(scalar_states()); expected = {(s, o) for s in states for o in ("M", "Mt")}
    seen = set(); refs = 0; excluded = set(); open_ = set()

    def check_lower(h, y, F, ori, least, greatest, claimed):
        nonlocal refs
        assert type(claimed) is int and least <= claimed <= greatest + 1, ("bound out of range", claimed, least, greatest)
        for s in range(least, min(claimed - 1, greatest) + 1):
            for q in range(s + 1):
                z = s - q
                if 2 * h + y + z + comb(q, 2) < 32: continue
                key = (h, y, F, ori, q, z)
                if direct(key): continue
                assert key in certs, ("missing certificate", key)
                refs += 1

    for c in data["claims"]:
        st = tuple(c["state"]); ori = c["orientation"]; ident = (st, ori)
        assert ident in expected and ident not in seen; seen.add(ident)
        if not c["excluded"]:
            open_.add(ident); continue
        a, b, Y, V, he, ho, le, lo, Se, So, budget = st
        k, l = c["lower_even"], c["lower_odd"]
        check_lower(he, Y, V, ori, le, Se, k)
        check_lower(ho, V, Y, "Mt" if ori == "M" else "M", lo, So, l)
        assert k > Se or l > So or k + l > budget, ("final test does not fail", ident, k, l)
        excluded.add(ident)
    assert seen == expected
    res = {"gates": G, "scalar_states": len(states), "claims": len(seen), "excluded_certified": len(excluded), "open": len(open_),
           "certificates": len(certs), "coefficients_checked": coeffs, "certificate_references": refs, "largest_weighted_rhs": maxrhs,
           "uncertified_keys_reported_by_generator": len(data.get("uncertified_keys", []))}
    # cross-file accounting when run inside the repository layout
    acc = HERE / "published_sets.json"
    if acc.exists():
        P = json.load(open(acc)); pub = {n: {(tuple(s), o) for s, o in v} for n, v in P.items()}
        union = set().union(*pub.values())
        res["disjoint_from_published_sets"] = not (excluded & union)
        res["excluded_plus_published_equals_domain"] = (excluded | union) == expected
        res["open_here_equals_union_of_published_sets"] = open_ == union
        res["published_set_sizes"] = {n: len(v) for n, v in pub.items()}
    print(json.dumps(res, indent=1))
    json.dump(res, open(HERE / "CHECKED_PKG75_G75.json", "w"), indent=1)
    assert res["excluded_certified"] == 5908 and res["open"] == 1508, "unexpected counts"
    print("PASSED: 5,908 package-row exclusions at G = 75 have exact certificates and complete key coverage; 1,508 claims are open under the package rows.")


if __name__ == "__main__":
    main()
