#!/usr/bin/env python3
"""qcert3: INDEPENDENT checker for CERTIFICATES_CASES75_B3.json (G = 75): per-case Farkas certificates for the full
local systems (package + batch-1 + PK4/PK5 + FM7/FM9 + the HUB2 split of Lemma H2 + the DARK split q_D = 0..q), and
the case-enumerating coverage check.

Standard library only; nothing imported from the generator, from qhub, qhubcheck, qreal, qrealcheck, qbound or the
package programs.  Every row constant and every column coefficient is written out here by hand, column by column
(the style of the package's independent75.py; the hand-written package, batch-1 and DARK rows of qcert's
check_ext75.py / qcert2's check_cases75.py are reused verbatim).  The new blocks are written from their statements in
PROOF_ADDENDUM_3.md, not from the generator:
  PK4 / PK5    (C.5) #{u >= 3} <= 1 at q = 4;  n_3 + 2 n_4 + 2 n_5 <= 2 at q = 5  (n_j = #{u = j})
  FM7 / FM9    (C.6) W + y_1 <= 7 (q - A) + top(A), Z <= 3 (q - A) + top3(A), linearised by the chords through
               (a0, a0 + 1), a0 = 0..q-1, with top / top3 built here from the PINNED rank histogram of finite fact FM
               (recomputed from the matrix by fm_tab3.py);
  HUB2         (C.4) in the case A = a (a = 2..q) the types with r <= 2 and u > (3 - r) + (q - a) are deleted and
               sum_{r=3} u n = a is added (two inequalities); in the case A <= 1 the row sum_{r=3} u n <= 1 is added.

For each certificate (key, hub, dark, lambda):
    the case is legal for the key (hub = None if q <= 1, else ("eq", a) with 2 <= a <= q or ("le", 1); dark = None or
    0 <= dark <= q); lambda is a list of nonnegative integers of the right length; lambda^T b < 0; and lambda^T A >= 0
    in every column of the case: the helper types (r,u,v) with r+u+v >= 3, 0<=r<=3, 0<=u<=q, 0<=v<=min(2z, h-1),
    MINUS (hub = ("eq", a)) the types with r <= 2 and u > 3 - r + q - a, and the auxiliary columns y0, y1, y2
    (+ y2d, Fb, Fd in a dark case).
Coverage (the case enumeration): a key is excluded iff for EVERY leaf (hc, d), hc over the hub cases of q and d over
0..q, some certificate of the key has (hub in {None, hc}) and (dark in {None, d}).  Checked for every killed key and
for every key referenced by a claim.
For each claim (state, orientation, k, l): the state lies in the admissible domain at G = 75; every (q,z) with
q+z < k on the even phase (q+z < l on the odd phase) that passes (4.4) and is not a direct exclusion (Lemma 10.3)
is a covered key; and k > S_e or l > S_o or k + l > a + b + 2G - 192.

usage: python3 check_cases3.py [CERTIFICATES_CASES75_B3.json] ['{}' to skip the pinned counts]
"""
import json, sys
from pathlib import Path

G = 75
KR = {0: 3, 1: 2, 2: 1}                    # Lemma H2: r_i + m_i <= 3
RHO6 = {'M': 20, 'Mt': 28}; RESERVE = {'M': 8, 'Mt': 4}; EPS = {'M': 2, 'Mt': 0}
# finite fact FM (pinned): rank(C_l) over the distinct labels f + c, f full, c in B; sorted decreasingly
FM_RANKS = {'M': [7] * 4 + [6] * 108 + [5] * 140 + [4] * 692 + [3] * 3696,
            'Mt': [6] * 216 + [5] * 144 + [4] * 1176 + [3] * 4960}


def c2(x): return x * (x - 1) // 2


def fm_top(ori, a): return sum(FM_RANKS[ori][:a])                          # the a largest ranks
def fm_top3(ori, a): return sum(min(3, r - 1) for r in FM_RANKS[ori][:a])  # the a largest values of min(3, rank - 1)


def hub_cases(q):
    """Lemma H2's split: A = sum_{r=3} u n is an integer in 0..q (L6); for q <= 1 the bound u_i <= 3 - r_i + q - A is
    vacuous (u_i <= q <= 3 - r_i + q - 1 for every r_i <= 2 and every A <= q), so no split; for q >= 2 the cases A = a
    (a = 2..q) and A <= 1 exhaust 0..q."""
    if q <= 1: return [None]
    return [('eq', a) for a in range(2, q + 1)] + [('le', 1)]


def legal_case(key, hub, dark):
    q = key[4]
    if hub is not None:
        if q <= 1: return False
        if not (isinstance(hub, (list, tuple)) and len(hub) == 2): return False
        if hub[0] == 'eq' and not (2 <= hub[1] <= q): return False
        if hub[0] == 'le' and hub[1] != 1: return False
        if hub[0] not in ('eq', 'le'): return False
    if dark is not None and not (type(dark) is int and 0 <= dark <= q): return False
    return True


def types_of(key, hub):
    h, y, F, ori, q, z = key
    out = []
    for r in range(4):
        for u in range(q + 1):
            for v in range(min(2 * z, max(0, h - 1)) + 1):
                if r + u + v < 3: continue
                if hub is not None and hub[0] == 'eq' and r <= 2 and u > KR[r] + (q - hub[1]): continue   # Lemma H2 in case A = a
                out.append((r, u, v))
    return out


def right_sides(key, hub=None, dark=None):
    """row constants b: package rows (independent75 order), batch-1 rows (check_ext75 order), flat batch-3 rows
    (PK, FM chords), hub rows, dark rows.  Returns (b, n_pkg, n_b1, n_flat)."""
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
    # ---- batch-1 rows (qcert)
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
    n_b1 = len(b) - n_pkg
    # ---- flat batch-3 rows: packing at q = 4, 5 (Lemma 10.4's argument), FM chords (finite fact FM)
    if q == 4: b.append(1)                         # PK4: two 3-subsets of a 4-set share two elements
    if q == 5: b.append(2)                         # PK5: n3 + 2 n4 + 2 n5 <= 2
    for a0 in range(q):                            # chord of A -> 7 (q - A) + top(A) through A = a0, a0 + 1 (concave: valid for all A)
        s = fm_top(ori, a0 + 1) - fm_top(ori, a0)
        b.append(7 * (q - a0) + fm_top(ori, a0) + (7 - s) * a0)     # FM7(a0): W + y1 + (7 - s) A <= ...
        s3 = fm_top3(ori, a0 + 1) - fm_top3(ori, a0)
        b.append(3 * (q - a0) + fm_top3(ori, a0) + (3 - s3) * a0)   # FM9(a0): Z + (3 - s3) A <= ...
    n_flat = len(b) - n_pkg - n_b1
    # ---- HUB2 case rows (Lemma H2): A = a as two inequalities, or A <= 1
    if hub is not None:
        if hub[0] == 'eq': b += [hub[1], -hub[1]]
        else: b.append(1)
    # ---- DARK case rows, exactly d dark labels (Addendum 2, B.3-B.4).  With dk = sum_bright k_l >= rho - y2 - z - D0 + d
    #      (Lemma G* with the F9 space J), the per-bright-label capacities summed over the q - d bright labels give
    #      (cap per label) * (q - d) - (multiple of dk); the lower bound on dk is substituted (its coefficient is negative).
    if dark is not None:
        d = dark; low = rho - z + d                # the constant part of the lower bound on dk (y2 and D0 move to the left)
        b.append(7 * (q - d) - 2 * low)            # L13d:  W + y1 <= 7 (q-d) - 2 dk
        b.append(7 * (q - d) + eps - 2 * low)      # L14d:  W + A + y1 <= 7 (q-d) + eps - 2 dk
        b.append(3 * (q - d) - low)                # L15d:  Z <= 3 (q-d) - dk
        if ori == 'M':
            b.append(6 * (q - d) - 3 * low)        # L17Md: 2Z + 2E + 3 dk <= 6 (q-d)
        else:
            b.append(3 * (q - d) - 3 * low)        # L17Td: Z + E + 3 dk <= 3 (q-d)
            b.append(7 * (q - d) - 3 * low)        # L18d:  W + A + 3 dk <= 7 (q-d)
        b.append(-(q - d))                         # bright lower: every bright label has an H-B edge at an anchored helper
        b.append(4 * (q - d))                      # bright capacity: anchored missing edges + kind-1 gates <= sum_bright (4 + 2 f_l) = 4 (q-d) + 2 Fb
        b.append(4 * d)                            # dark capacity: y2d <= sum_dark (4 + 2 f_l) = 4 d + 2 Fd
        b.append(F)                                # Fb + Fd + F_H <= F
        b.append(0)                                # y2d <= y2
        b.append(c2(q))                            # y2m = y2 - y2d <= C(q, 2)
        b.append(4 * q + 2 * F)                    # (I'): y1 + y2d + 2 y2m + U + 2 F_H <= 4q + 2F
        if d == q: b.append(0)                     # no bright label: Fb = 0
        if d == 0: b.append(0)                     # no dark label: Fd = y2d = 0
    return b, n_pkg, n_b1, n_flat


def type_column(key, hub, dark, r, u, v):
    h, y, F, ori, q, z = key
    degree = r + u + v
    f = max(0, (degree - 3) // 2)
    full = int(r == 3); excess = max(0, r - 1); anchored = int(r >= 1)
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
    # ---- batch-1 rows
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
    # ---- flat batch-3 rows
    if q == 4: col.append(int(u >= 3))             # PK4: every helper with u >= 3 counts once
    if q == 5: col.append((0, 0, 0, 1, 2, 2)[u])   # PK5: n3 + 2 n4 + 2 n5
    for a0 in range(q):
        s = fm_top(ori, a0 + 1) - fm_top(ori, a0)
        col.append(r * u + full * (7 - s) * u)     # FM7(a0): W (per type r u) + (7 - s) A (A = sum_{r=3} u n)
        s3 = fm_top3(ori, a0 + 1) - fm_top3(ori, a0)
        col.append(excess * u + full * (3 - s3) * u)   # FM9(a0): Z + (3 - s3) A
    # ---- HUB2 rows: A = sum_{r=3} u n
    if hub is not None:
        if hub[0] == 'eq': col += [full * u, -full * u]
        else: col.append(full * u)
    # ---- DARK rows
    if dark is not None:
        col += [r * u - 2 * deficit,               # L13d: W - 2 D0 (+ y1 - 2 y2)
                r * u + full * u - 2 * deficit,    # L14d: W + A - 2 D0 (+ y1 - 2 y2)
                excess * u - deficit]              # L15d: Z - D0 (- y2)
        if ori == 'M':
            col.append(2 * excess * u + 2 * overflow - 3 * deficit)      # L17Md: 2Z + 2E - 3 D0 (- 3 y2)
        else:
            col += [excess * u + overflow - 3 * deficit,                 # L17Td: Z + E - 3 D0 (- 3 y2)
                    r * u + full * u - 3 * deficit]                      # L18d: W + A - 3 D0 (- 3 y2)
        col.append(-anchored * u)                  # bright lower: - sum_{r>=1} u n <= -(q - d)
        col.append(anchored * u)                   # bright capacity: sum_{r>=1} u n + y1 - 2 Fb <= 4 (q - d)
        col.append(0)                              # dark capacity
        col.append(f)                              # F budget: F_H >= sum f_min n
        col.append(0)                              # y2d <= y2
        col.append(0)                              # y2m <= C(q,2)
        col.append(u + 2 * f)                      # (I'): U + 2 F_H
        if dark == q: col.append(0)
        if dark == 0: col.append(0)
    return col


def aux_columns(key, hub, dark, n_pkg):
    """columns y0, y1, y2 (and y2d, Fb, Fd in a dark case): zero on the package rows, then literal coefficients."""
    h, y, F, ori, q, z = key
    zero = [0] * n_pkg
    q0 = [0] if q == 0 else []
    if ori == 'M':
        y0 = zero + [1, -1, 0, 0, 1, 0, 0, 0] + [0] + [0] + q0
        y1 = zero + [1, -1, 0, 1, 0, 1, 1, 0] + [0] + [1] + q0
        y2 = zero + [1, -1, 0, 0, 0, -2, -2, -1] + [-3] + [1] + q0
    else:
        y0 = zero + [1, -1, 0, 0, 1, 0, 0, 0] + [0, 0, 0, 0] + q0 + [0] + q0
        y1 = zero + [1, -1, 0, 1, 0, 1, 1, 0] + [0, 0, 0, 0] + q0 + [1] + q0
        y2 = zero + [1, -1, 0, 0, 0, -2, -2, -1] + [-3, -3, -1, -3] + ([-1] if q == 0 else []) + [1] + q0
    cols = {'y0': y0, 'y1': y1, 'y2': y2}
    # flat batch-3 rows: PK (no even+even term); FM7 chords carry y1 (W + y1), FM9 chords carry nothing
    pk = [0] if q in (4, 5) else []
    cols['y0'] += pk + [0, 0] * q
    cols['y1'] += pk + [1, 0] * q
    cols['y2'] += pk + [0, 0] * q
    if hub is not None:
        nh = 2 if hub[0] == 'eq' else 1
        for c in cols.values(): c += [0] * nh
    if dark is not None:
        d = dark
        n17 = 1 if ori == 'M' else 2                         # L17Md | L17Td, L18d
        tail = ([0] if d == q else []) + ([0] if d == 0 else [])
        #            L13d L14d L15d  L17(.)        bl  bc  dc  Fb+Fd  y2d<=y2  y2m  I'
        cols['y0'] += [0, 0, 0] + [0] * n17 + [0, 0, 0, 0, 0, 0, 0] + tail
        cols['y1'] += [1, 1, 0] + [0] * n17 + [0, 1, 0, 0, 0, 0, 1] + tail
        cols['y2'] += [-2, -2, -1] + [-3] * n17 + [0, 0, 0, 0, -1, 1, 2] + tail
        # the three dark columns: zero on every row before the dark block
        pre = len(cols['y0']) - (10 + n17 + len(tail))
        cols['y2d'] = [0] * pre + [0, 0, 0] + [0] * n17 + [0, 0, 1, 0, 1, -1, -1] + ([0] if d == q else []) + ([1] if d == 0 else [])
        cols['Fb'] = [0] * pre + [0, 0, 0] + [0] * n17 + [0, -2, 0, 1, 0, 0, 0] + ([1] if d == q else []) + ([0] if d == 0 else [])
        cols['Fd'] = [0] * pre + [0, 0, 0] + [0] * n17 + [0, 0, -2, 1, 0, 0, 0] + ([0] if d == q else []) + ([1] if d == 0 else [])
    return cols


def matrix(key, hub, dark):
    """(b, columns, n_pkg, n_b1, n_flat) with columns = [(label, column vector)] over all helper types of the case and the aux columns."""
    b, n_pkg, n_b1, n_flat = right_sides(key, hub, dark)
    cols = [((r, u, v), type_column(key, hub, dark, r, u, v)) for r, u, v in types_of(key, hub)]
    for name, col in aux_columns(key, hub, dark, n_pkg).items(): cols.append((name, col))
    for lab, col in cols: assert len(col) == len(b), ('column length', key, hub, dark, lab, len(col), len(b))
    return b, cols, n_pkg, n_b1, n_flat


def check_weights(weights, b, cols):
    assert isinstance(weights, list) and all(type(w) is int and w >= 0 for w in weights), 'weights must be nonnegative integers'
    assert len(weights) == len(b), ('length', len(weights), len(b))
    wrhs = sum(w * bi for w, bi in zip(weights, b))
    assert wrhs < 0, ('weighted right-hand side not negative', wrhs)
    for lab, col in cols:
        s = sum(w * c for w, c in zip(weights, col))
        assert s >= 0, ('negative column coefficient', lab, s)
    return len(cols), wrhs


def check_certificate(key, hub, dark, weights):
    """raises AssertionError on any failure; returns (columns checked, weighted rhs, n_pkg, n_b1, n_flat)."""
    h, y, F, ori, q, z = key
    assert ori in ('M', 'Mt') and all(type(v) is int and v >= 0 for v in (h, y, F, q, z))
    assert legal_case(key, hub, dark), ('illegal case', key, hub, dark)
    b, cols, n_pkg, n_b1, n_flat = matrix(key, hub, dark)
    count, wrhs = check_weights(weights, b, cols)
    return count, wrhs, n_pkg, n_b1, n_flat


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


def leaves(q):
    return [(hc, d) for hc in hub_cases(q) for d in range(q + 1)]


def covered(cases, q):
    """cases: the set of (hub, dark) certified for a key.  True iff every leaf is covered."""
    if (None, None) in cases: return True
    for hc, d in leaves(q):
        if (hc, None) in cases or (None, d) in cases or (hc, d) in cases: continue
        return False
    return True


STATES = [None]
def claims_check(claims, certs):
    """coverage and final test of each claim against certs = {key: set of certified (hub, dark) cases}.
    Returns (seen, references, direct, distinct); raises AssertionError on any failure."""
    if STATES[0] is None: STATES[0] = scalar_domain()
    states = STATES[0]
    seen = set(); references = 0; direct = 0; distinct = set()
    for claim in claims:
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
                    assert covered(certs[key], q), ('referenced key not covered in every case', (st, ori), key)
                    references += 1; distinct.add(key)
        assert k > Sa or l > Sb or k + l > budget, ('final test fails', st, ori, k, l)
    return seen, references, direct, distinct


def verify(data, quiet=False):
    assert data['gates'] == G
    certs = {}; coefficients = 0; rhs_values = []; kinds = {'package': 0, 'batch1': 0, 'flat': 0, 'case': 0}
    case_kinds = {'hub-only': 0, 'dark-only': 0, 'hub+dark': 0}; hub_values = {}; dark_values = {}; flat_rows = {'PK': 0, 'FM': 0}
    for entry in data['certificates']:
        key = tuple(entry['key']); hub = tuple(entry['hub']) if entry.get('hub') is not None else None; dark = entry.get('dark')
        count, wrhs, n_pkg, n_b1, n_flat = check_certificate(key, hub, dark, entry['weights'])
        kind = entry.get('kind'); w = entry['weights']
        if kind == 'package':
            assert hub is None and dark is None and not any(w[n_pkg:]), ('a "package" certificate uses a non-package row', key)
        elif kind == 'batch1':
            assert hub is None and dark is None and any(w[n_pkg:n_pkg + n_b1]) and not any(w[n_pkg + n_b1:]), ('a "batch1" certificate misuses rows', key)
        elif kind == 'flat':
            assert hub is None and dark is None and any(w[n_pkg + n_b1:n_pkg + n_b1 + n_flat]), ('a "flat" certificate uses no PK / FM row', key)
        elif kind == 'case':
            assert hub is not None or dark is not None, ('a "case" certificate without a case', key)
            if hub is not None and dark is not None: case_kinds['hub+dark'] += 1
            elif hub is not None: case_kinds['hub-only'] += 1
            else: case_kinds['dark-only'] += 1
            if hub is not None: hub_values[hub] = hub_values.get(hub, 0) + 1
            if dark is not None: dark_values[dark] = dark_values.get(dark, 0) + 1
        else:
            raise AssertionError(('unknown kind', key, kind))
        q = key[4]
        if q in (4, 5) and w[n_pkg + n_b1]: flat_rows['PK'] += 1
        if any(w[n_pkg + n_b1 + (1 if q in (4, 5) else 0):n_pkg + n_b1 + n_flat]): flat_rows['FM'] += 1
        kinds[kind] += 1
        cs = certs.setdefault(key, set())
        assert (hub, dark) not in cs, ('duplicate certificate', key, hub, dark)
        cs.add((hub, dark))
        coefficients += count; rhs_values.append(wrhs)
    # key bookkeeping: batch-2-feasible = killed + surviving, disjoint; the baseline 381 inside it
    b2 = {tuple(k) for k in data['batch2_feasible_keys']}; killed = {tuple(k) for k in data['killed_keys']}; surv = {tuple(k) for k in data['surviving_keys']}
    base = {tuple(k) for k in data['baseline_keys']}
    assert killed <= b2 and surv <= b2 and not (killed & surv) and killed | surv == b2, 'killed / surviving keys do not partition the batch-2-feasible keys'
    assert base <= b2
    bkilled = {tuple(k) for k in data['baseline_killed_keys']}; bsurv = {tuple(k) for k in data['baseline_surviving_keys']}
    assert bkilled == base & killed and bsurv == base & surv, 'baseline killed / surviving lists inconsistent'
    n_leaves_killed = 0
    for key in sorted(killed):
        assert key in certs, ('killed key without certificate', key)
        assert covered(certs[key], key[4]), ('killed key not covered in every case', key, sorted(certs[key], key=str))
        n_leaves_killed += len(leaves(key[4]))
    # claims
    seen, references, direct, distinct = claims_check(data['claims'], certs)
    n_leaves_ref = sum(len(leaves(key[4])) for key in distinct)
    by_kind_keys = {'package': 0, 'batch1': 0, 'flat': 0, 'case': 0}
    for key, cs in certs.items():
        if (None, None) in cs:
            b_, n_pkg, n_b1, n_flat = right_sides(key)
            w = next(e['weights'] for e in data['certificates'] if tuple(e['key']) == key and e.get('hub') is None and e.get('dark') is None)
            by_kind_keys['package' if not any(w[n_pkg:]) else ('batch1' if not any(w[n_pkg + n_b1:]) else 'flat')] += 1
        else: by_kind_keys['case'] += 1
    result = dict(gates=G, scalar_states=len(STATES[0]), claims_checked=len(seen), certificates=sum(kinds.values()),
                  certificates_package=kinds['package'], certificates_batch1=kinds['batch1'], certificates_flat=kinds['flat'], certificates_case=kinds['case'],
                  case_certificates_hub_only=case_kinds['hub-only'], case_certificates_dark_only=case_kinds['dark-only'],
                  case_certificates_hub_and_dark=case_kinds['hub+dark'], certificates_using_PK=flat_rows['PK'], certificates_using_FM=flat_rows['FM'],
                  keys_with_certificates=len(certs), keys_by_kind=by_kind_keys,
                  batch2_feasible_keys=len(b2), killed_keys=len(killed), surviving_keys=len(surv),
                  baseline_keys=len(base), baseline_killed=len(bkilled), baseline_surviving=len(bsurv),
                  leaf_cases_of_killed_keys=n_leaves_killed, leaf_cases_of_referenced_keys=n_leaves_ref,
                  coefficients_checked=coefficients, largest_right_side=max(rhs_values) if rhs_values else None,
                  certificate_references=references, distinct_referenced=len(distinct), direct_geometric_references=direct,
                  hub_case_histogram={str(k): v for k, v in sorted(hub_values.items(), key=str)},
                  dark_case_histogram={str(k): v for k, v in sorted(dark_values.items())}, all_checks_passed=True)
    if not quiet: print(json.dumps(result, indent=2))
    return result


EXPECTED = {'scalar_states': 3708, 'claims_checked': 207, 'certificates': 4950, 'certificates_package': 1615, 'certificates_batch1': 220,
            'certificates_flat': 190, 'certificates_case': 2925, 'case_certificates_hub_only': 1611, 'case_certificates_dark_only': 14,
            'case_certificates_hub_and_dark': 1300, 'certificates_using_PK': 540, 'certificates_using_FM': 47, 'keys_with_certificates': 2471,
            'batch2_feasible_keys': 1713, 'killed_keys': 536, 'surviving_keys': 1177, 'baseline_keys': 381, 'baseline_killed': 265, 'baseline_surviving': 116,
            'leaf_cases_of_killed_keys': 14312, 'leaf_cases_of_referenced_keys': 27153, 'coefficients_checked': 251213, 'largest_right_side': -1,
            'certificate_references': 3353, 'distinct_referenced': 2054, 'direct_geometric_references': 401}   # pinned 2026-11-08, see REPORT.md

if __name__ == '__main__':
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name('CERTIFICATES_CASES75_B3.json')
    data = json.loads(src.read_text())
    res = verify(data)
    exp = json.loads(sys.argv[2]) if len(sys.argv) > 2 else EXPECTED
    if exp:
        for k, v in exp.items():
            assert res[k] == v, ('expected', k, v, 'got', res[k])
        print('expected counts match:', exp)
    Path(__file__).with_name('CHECKED_CASES75_B3.json').write_text(json.dumps(res, indent=2) + '\n')
    print('INDEPENDENT CHECK PASSED')
