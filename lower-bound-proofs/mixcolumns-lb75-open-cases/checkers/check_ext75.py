#!/usr/bin/env python3
"""qcert: INDEPENDENT checker for CERTIFICATES_EXT75.json (G = 75).

Standard library only; nothing imported from the generator, from qbound, or from the package programs.
Every row constant and every column coefficient of the extended local system is written out here by hand,
in the style of the package's independent75.py; the scalar domain and the coverage obligations are rebuilt
from the formulas of PROOF.md section 11 at G = 75.

For each certificate (key, lambda):
    lambda is a list of nonnegative integers of the right length,
    lambda^T b < 0, and lambda^T A >= 0 in every column: all helper types (r,u,v) with r+u+v >= 3,
    0<=r<=3, 0<=u<=q, 0<=v<=min(2z, h-1), and the three columns y0, y1, y2.
For each claim (state, orientation, k, l): the state lies in the admissible domain at G = 75; every (q,z)
with q+z < k on the even phase (q+z < l on the odd phase) that passes (4.4) and is not a direct exclusion
(Lemma 10.3) has a certificate; and k > S_e or l > S_o or k + l > a + b + 2G - 192.

usage: python3 check_ext75.py [CERTIFICATES_EXT75.json]
"""
import json, sys
from pathlib import Path

G = 75
RHO6 = {'M': 20, 'Mt': 28}; RESERVE = {'M': 8, 'Mt': 4}; EPS = {'M': 2, 'Mt': 0}


def c2(x): return x * (x - 1) // 2


def right_sides(key):
    """row constants b, package rows first (independent75 order), then the new rows."""
    h, y, F, ori, q, z = key
    rho6, rho, eps = RHO6[ori], RESERVE[ori], EPS[ori]
    td = 32 + h - y + q + z
    b = [h, -h, td, -td, 2 * z, -2 * z,
         F, c2(q), q, 7 * q, 3 * h + 2 * F + y - 32, 3 * q, 4 * q + 2 * F, q + z, rho6,
         2 * y + 2 * z + 7 * q - 2 * rho, 2 * y + 2 * z + 7 * q - 2 * rho + eps, y + z + 3 * q - rho, 3 * q]
    if ori == 'M':
        b.append(3 * y + 3 * z + 6 * q - 24)
    else:
        b += [3 * y + 3 * z + 3 * q - 12, 3 * y + 3 * z + 7 * q - 12, y - 3, 3 * y + 2 * z - 9]
        if q == 0: b += [-1, y - 3]
    if q == 6: b.append(4)
    if q == 7: b.append(14)
    n_pkg = len(b)
    # ---- new rows
    b += [y, -y]                                   # y0 + y1 + y2 = y
    b.append(G - 32 - h - q)                       # N1: 3 n3 <= x + y - q = G - 32 - h - q
    b.append(7 * q)                                # L7*: W + y1 <= 7q
    b.append(rho6)                                 # L12*: sum (r-1)+ n + y0 <= rho6
    b += [2 * z + 7 * q - 2 * rho, 2 * z + 7 * q - 2 * rho + eps, z + 3 * q - rho]   # L13*, L14*, L15* (y -> y2)
    if ori == 'M':
        b.append(3 * z + 6 * q - 24)               # L17-M*
    else:
        b += [3 * z + 3 * q - 12, 3 * z + 7 * q - 12, -3, 2 * z - 9]   # L17-Mt*, L18*, L19*, L20*
        if q == 0: b.append(-3)                    # L22*
    b.append(4 * q + 2 * F)                        # (I): sum (u + 2 fmin) n + y1 + y2 <= 4q + 2F
    if q == 0: b.append(z - (32 - rho6))           # (Q0): sum_{r=0} n <= z - (32 - rho6)
    return b, n_pkg


def type_column(key, r, u, v):
    h, y, F, ori, q, z = key
    degree = r + u + v
    f = max(0, (degree - 3) // 2)
    full = int(r == 3); excess = max(0, r - 1)
    deficit = (u - 1) * int(r == 0); overflow = max(0, u - 2) * full
    col = [1, -1, degree, -degree, v, -v,
           f, c2(u), full * u, r * u, full * (1 + 2 * f), excess * u, u + 2 * f, full * (u + v), excess,
           r * u - 2 * deficit, r * u + full * u - 2 * deficit, excess * u - deficit, excess * u + overflow]
    if ori == 'M':
        col.append(2 * excess * u + 2 * overflow - 3 * deficit)
    else:
        col += [excess * u + overflow - 3 * deficit, r * u + full * u - 3 * deficit,
                -(u + v - 1) * int(r == 0) - v * int(r == 1), -(3 * u + v - 3) * int(r == 0)]
        if q == 0: col += [-int(r == 0), -(v - 1) * int(r == 0)]
    if q == 6: col.append((0, 0, 0, 1, 3, 4, 4)[u])
    if q == 7: col.append((0, 0, 0, 2, 7, 12, 14, 14)[u])
    # ---- new rows
    col += [0, 0]                                  # y split
    col.append(3 * full)                           # N1
    col.append(r * u)                              # L7*
    col.append(excess)                             # L12*
    col += [r * u - 2 * deficit, r * u + full * u - 2 * deficit, excess * u - deficit]   # L13*, L14*, L15*
    if ori == 'M':
        col.append(2 * excess * u + 2 * overflow - 3 * deficit)
    else:
        col += [excess * u + overflow - 3 * deficit, r * u + full * u - 3 * deficit,
                -(u + v - 1) * int(r == 0) - v * int(r == 1), -(3 * u + v - 3) * int(r == 0)]
        if q == 0: col.append(-(v - 1) * int(r == 0))
    col.append(u + 2 * f)                          # (I)
    if q == 0: col.append(int(r == 0))             # (Q0)
    return col


def aux_columns(key, n_pkg):
    """columns y0, y1, y2: zero on the package rows, then their coefficients in the new rows."""
    h, y, F, ori, q, z = key
    zero = [0] * n_pkg
    if ori == 'M':
        tailM = lambda c17: [c17]
        y0 = zero + [1, -1, 0, 0, 1, 0, 0, 0] + tailM(0) + [0] + ([0] if q == 0 else [])
        y1 = zero + [1, -1, 0, 1, 0, 1, 1, 0] + tailM(0) + [1] + ([0] if q == 0 else [])
        y2 = zero + [1, -1, 0, 0, 0, -2, -2, -1] + tailM(-3) + [1] + ([0] if q == 0 else [])
    else:
        y0 = zero + [1, -1, 0, 0, 1, 0, 0, 0] + [0, 0, 0, 0] + ([0] if q == 0 else []) + [0] + ([0] if q == 0 else [])
        y1 = zero + [1, -1, 0, 1, 0, 1, 1, 0] + [0, 0, 0, 0] + ([0] if q == 0 else []) + [1] + ([0] if q == 0 else [])
        y2 = zero + [1, -1, 0, 0, 0, -2, -2, -1] + [-3, -3, -1, -3] + ([-1] if q == 0 else []) + [1] + ([0] if q == 0 else [])
    return [y0, y1, y2]


def check_certificate(key, weights):
    """raises AssertionError on any failure; returns (columns checked, weighted rhs, n_pkg)."""
    h, y, F, ori, q, z = key
    assert ori in ('M', 'Mt')
    assert all(type(v) is int and v >= 0 for v in (h, y, F, q, z))
    assert isinstance(weights, list) and all(type(w) is int and w >= 0 for w in weights), 'weights must be nonnegative integers'
    b, n_pkg = right_sides(key)
    assert len(weights) == len(b), ('length', key, len(weights), len(b))
    wrhs = sum(w * bi for w, bi in zip(weights, b))
    assert wrhs < 0, ('weighted right-hand side not negative', key, wrhs)
    count = 0
    for r in range(4):
        for u in range(q + 1):
            for v in range(min(2 * z, max(0, h - 1)) + 1):
                if r + u + v < 3: continue
                col = type_column(key, r, u, v)
                assert len(col) == len(weights)
                s = sum(w * c for w, c in zip(weights, col))
                assert s >= 0, ('negative column coefficient', key, (r, u, v), s)
                count += 1
    for name, col in zip(('y0', 'y1', 'y2'), aux_columns(key, n_pkg)):
        assert len(col) == len(weights), (name, len(col), len(weights))
        s = sum(w * c for w, c in zip(weights, col))
        assert s >= 0, ('negative column coefficient', key, name, s)
        count += 1
    return count, wrhs, n_pkg


def least_s(h, y):
    for s in range(65):
        if any(2 * h + y + (s - q) + c2(q) >= 32 for q in range(s + 1)): return s
    raise AssertionError


def scalar_domain():
    states = set()
    for a in range(24, G - 44):
        for b in range(24, G - 31):
            for Y in range(G - 31 - a):
                ha = G - 32 - a - Y
                for V in range(min(Y, G - 32 - b) + 1):
                    hb = G - 32 - b - V
                    if hb + Y < 13: continue
                    Sa = min(3 * ha + 2 * V + Y - 32, 2 * b - a + G - 96 + V)
                    Sb = min(3 * hb + 2 * Y + V - 32, 2 * a - b + G - 96 + Y)
                    if Sa < 0 or Sb < 0: continue
                    la, lb = least_s(ha, Y), least_s(hb, V)
                    budget = a + b + 2 * G - 192
                    if la <= Sa and lb <= Sb and la + lb <= budget:
                        states.add((a, b, Y, V, ha, hb, la, lb, Sa, Sb, budget))
    return states


def geometric_exclusion(key):
    _, _, _, ori, q, z = key
    if q != 0: return False
    return z == 0 or (ori == 'Mt' and z <= 7)


def verify(data, quiet=False):
    assert data['gates'] == G
    certs = {}; coefficients = 0; rhs_values = []; kinds = {'new': 0, 'package': 0}
    for entry in data['certificates']:
        key = tuple(entry['key']); assert key not in certs, ('duplicate', key)
        count, wrhs, n_pkg = check_certificate(key, entry['weights'])
        kind = entry.get('kind')
        if kind == 'new':
            assert any(entry['weights'][n_pkg:]), ('a "new" certificate uses no new row', key)
        elif kind == 'package':
            assert not any(entry['weights'][n_pkg:]), ('a "package" certificate uses a new row', key)
        else:
            raise AssertionError(('unknown kind', key, kind))
        kinds[kind] += 1
        coefficients += count; rhs_values.append(wrhs); certs[key] = entry['weights']
    states = scalar_domain()
    seen = set(); references = 0; direct = 0; distinct = set(); ref_new = set(); ref_pkg = set()
    for claim in data['claims']:
        st, ori = tuple(claim['state']), claim['orientation']
        assert st in states, ('state outside the admissible domain', st)
        assert (st, ori) not in seen; seen.add((st, ori))
        a, b, Y, V, ha, hb, la, lb, Sa, Sb, budget = st
        k, l = claim['lower_even'], claim['lower_odd']
        assert type(k) is int and type(l) is int
        assert la <= k <= Sa + 1 and lb <= l <= Sb + 1, (st, ori, k, l)
        other = 'Mt' if ori == 'M' else 'M'
        for h, y, F, o, low, cap, bound in ((ha, Y, V, ori, la, Sa, k), (hb, V, Y, other, lb, Sb, l)):
            for total in range(low, min(cap, bound - 1) + 1):
                for z in range(total + 1):
                    q = total - z
                    if 2 * h + y + z + c2(q) < 32: continue
                    key = (h, y, F, o, q, z)
                    if geometric_exclusion(key):
                        direct += 1; continue
                    assert key in certs, ('uncovered key', (st, ori), key)
                    references += 1; distinct.add(key)
        assert k > Sa or l > Sb or k + l > budget, ('final test fails', st, ori, k, l)
    for key in distinct:
        (ref_new if any(certs[key][right_sides(key)[1]:]) else ref_pkg).add(key)
    result = dict(gates=G, scalar_states=len(states), claims_checked=len(seen), local_certificates=len(certs),
                  certificates_new=kinds['new'], certificates_package=kinds['package'],
                  coefficients_checked=coefficients, largest_right_side=max(rhs_values) if rhs_values else None,
                  certificate_references=references, distinct_referenced=len(distinct),
                  distinct_referenced_new=len(ref_new), distinct_referenced_package=len(ref_pkg),
                  direct_geometric_references=direct, all_checks_passed=True)
    if not quiet: print(json.dumps(result, indent=2))
    return result


EXPECTED = {'scalar_states': 3708, 'claims_checked': 195, 'local_certificates': 1772, 'certificates_new': 666,
            'certificates_package': 1106, 'coefficients_checked': 53917, 'largest_right_side': -1,
            'certificate_references': 2158, 'distinct_referenced': 1459, 'distinct_referenced_new': 353,
            'distinct_referenced_package': 1106, 'direct_geometric_references': 567}   # pinned 2026-11-07, see REPORT.md

if __name__ == '__main__':
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / 'certificates' / 'CERTIFICATES_EXT75.json'
    data = json.loads(src.read_text())
    res = verify(data)
    exp = json.loads(sys.argv[2]) if len(sys.argv) > 2 else EXPECTED
    if exp:
        for k, v in exp.items():
            assert res[k] == v, ('expected', k, v, 'got', res[k])
        print('expected counts match:', exp)
    Path(__file__).with_name('CHECKED_EXT75.json').write_text(json.dumps(res, indent=2) + '\n')
    print('INDEPENDENT CHECK PASSED')
