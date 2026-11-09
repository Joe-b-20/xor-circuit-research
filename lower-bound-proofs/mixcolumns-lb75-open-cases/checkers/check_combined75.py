#!/usr/bin/env python3
"""recon-check: INDEPENDENT checker for the combined certificates CERTIFICATES_COMBINED75.json (+ the J1-free addendum)
of the reconciliation audit (recon/), G = 75.

Each certificate is a nonnegative integer vector lambda over the rows of a CASE SYSTEM of the combined system
   [sprint qcert4 case system of (key, hub, dark)]  followed by  [push5 rows]  followed by  [push6 rows],
and must satisfy lambda^T A >= 0 on every column (helper types kept in the case + the sprint's auxiliary columns) and
lambda^T b <= -1.  The sprint part of the matrix is built by the repository's independent checkers
(lower-bound-proofs/mixcolumns-lb75-open-cases/checkers/check_cases4.py, which imports check_cases3_copy.py); these were
written independently of the sprint's generators.  The push5 / push6 rows are written HERE, from the proof texts of the
October archive (push5/odd_spine/FULL_HELPER_LABEL_OWNERSHIP_INDEPENDENT.txt, push5/global_chronology/HH_DEGREE_REALIZABILITY.txt,
push5/even_frontier/EE_QUOTIENT_CHARGE_THEOREM.txt, push6/global_chronology/REPEATED_CONTACT_CORE_PROOF.txt,
P_COUPLED_RESOURCE_ROWS.txt, ROUNDED_CLASS_CORE_PROOF.txt, push6/even_frontier/HH_EXCEPTIONAL_LABEL_BUDGET.txt,
HH_LABEL_MATCHING_REFINEMENTS.txt, FULL_PAIR_HH_ZERO_QUOTIENT.txt) and from the archive generators
push{5,6}/global_chronology/model_full_cuts.py (row ORDER, gcd normalisation and deduplication follow the generator, since
the certificates index rows by position).  Nothing is imported from recon/push_rows.py or from any generator.

Coverage: for each excluded claim (state, orientation, k, l): the state is in the scalar domain at G = 75 (own enumeration,
compared with check_cases3_copy.scalar_domain), la <= k <= Sa+1, lb <= l <= Sb+1; every key (h, y, F, ori, q, z) with
q + z < k on the even phase (q + z < l on the odd phase), q + z >= the least admissible s, passing the incidence test
2h + y + z + C(q,2) >= 32 and not directly excluded (q = 0 and (z = 0 or (Mt and z < 8))) has a certificate for the whole
key or for every leaf (A = a, q_D = d) of its case tree (a, d in 0..q); and k > Sa or l > Sb or k + l > a + b + 2G - 192.

usage: python3 check_combined75.py [CERTIFICATES_COMBINED75.json] [CERTIFICATES_COMBINED75_J1FREE_ADDENDUM.json] ['{}' to skip pinned counts]
"""
import json, sys, time
from math import comb, gcd
from fractions import Fraction
from pathlib import Path
from collections import Counter
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
CHK = HERE
RECON = HERE.parent / "combined"
sys.path.insert(0, str(CHK))
import check_cases4 as c4          # noqa: E402  (repository checker; hub cases ('eq', a), a = 0..q; joint rows P1..P5, LIM)
c3 = c4.c3                          # check_cases3_copy: package, batch-1, flat, hub, dark rows, aux columns
G = 75
NJ = c4.NJ                          # 7 joint rows, LIM last


# ----------------------------------------------------------------------------------------------- the package type list
def package_types(key):
    h, y, F, ori, q, z = key
    return [(r, u, v) for r in range(4) for u in range(q + 1) for v in range(min(2 * z, max(0, h - 1)) + 1) if r + u + v >= 3]


# ----------------------------------------------------------------------------------------------- push5 rows (own transcription)
def push5_rows(key, types, G=G):
    """[(name, coefficients over `types`, bound)] in the archive generator's order.
    Notation: N3 = #helpers with r = 3, N2 = #r = 2, A = sum_{r=3} u n, Z = sum (r-1)_+ u n, E = sum_{r=3} (u-2)_+ n,
    h0 = #r = 0, x = G - 32 - h - y (OO gates), t = 5 (M) / 7 (Mt) output-bit classes, C = 4t core outputs."""
    h, y, F, ori, q, z = key
    x = G - 32 - h - y
    t = 5 if ori == "M" else 7
    C = 4 * t
    rows = []
    # P5.1  HH_DEGREE_REALIZABILITY: no loops, so a helper meets at most z of the z H-H edges: n_(r,u,v) = 0 for v > z.
    rows.append(("new HH degree realizability <=", [int(v > z) for r, u, v in types], 0))
    # P5.2  FULL_HELPER_LABEL_OWNERSHIP sections 2, 4: <= 2 full helpers per class (rank-4 excess span) -> N3 <= 2t;
    #       OO ownership x >= 5 N3 - 4t -> N3 <= floor((x + C)/5).
    rows.append(("new full helper chronological cap <=", [int(r == 3) for r, u, v in types], min(2 * t, (x + C) // 5)))
    # P5.3  section 3: the 3 N3 reference labels are distinct and represented; with the q missing labels, 3 N3 + q <= x + y.
    rows.append(("new full helper distinct represented labels <=", [int(r == 3) for r, u, v in types], (x + y - q) // 3))
    # P5.4  section 5: L + N2 + 2 N3 <= x + C (birth ownership in the core) and L >= 3 N3.
    rows.append(("new repeated helper joint birth ownership <=", [int(r == 2) + 5 * int(r == 3) for r, u, v in types], x + C))
    if ori == "Mt":
        # P5.5 / P5.6  EE_QUOTIENT_CHARGE_THEOREM section 6 (7b): h0 = 0 forces an exceptional label (F1, dim R10 = 29),
        #       so p <= q - 1 + h0; with A <= p and Z + E <= 3p.
        rows.append(("new transpose full missing unanchored coupling <=", [(u if r == 3 else 0) - int(r == 0) for r, u, v in types], q - 1))
        rows.append(("new transpose weighted excess unanchored coupling <=",
                     [max(0, r - 1) * u + (max(0, u - 2) if r == 3 else 0) - 3 * int(r == 0) for r, u, v in types], 3 * (q - 1)))
    if ori == "Mt" and z == 0:
        # P5.7 / P5.8  sections 4-6 ((7), (7a)): z = 0 -> >= 1 exceptional label; z = 0 and q <= 6 -> >= 2.
        exc = 2 if q <= 6 else 1
        rows.append(("new transpose full missing exceptional colors <=", [u if r == 3 else 0 for r, u, v in types], q - exc))
        rows.append(("new transpose weighted excess exceptional colors <=",
                     [max(0, r - 1) * u + (max(0, u - 2) if r == 3 else 0) for r, u, v in types], 3 * (q - exc)))
    return rows


# ----------------------------------------------------------------------------------------------- push6 rows (own transcription)
def q_eff_of(key):
    """constant upper bound on p (number of repeated-bright missing labels): p <= q always; Mt and z <= 2: theorem (T) of
    HH_EXCEPTIONAL_LABEL_BUDGET forces an exceptional label (p <= q - 1); Mt, z = 0, q <= 6: EE_QUOTIENT_CHARGE sections 4-6
    force two (p <= q - 2)."""
    h, y, F, ori, q, z = key
    qe = q
    if ori == "Mt" and z <= 2: qe = q - 1
    if ori == "Mt" and z == 0 and q <= 6: qe = q - 2
    return qe


def overload_ratios(q):
    largest = max(4, q + 2)
    return sorted({Fraction(a, d) for d in range(1, largest + 1) for a in range(1, d + 1)})


def push6_rows(key, types, G=G, dedup=True):
    """Every push6 row is  s*K(n) - c*g(n) <= s*base + c*b  from a RESOURCE  K(n) <= base + c*p  and a BUDGET  s*p - g(n) <= b
    (P_COUPLED_RESOURCE_ROWS section 3), gcd-normalised and deduplicated by coefficient vector (smallest bound kept, first
    position kept), plus the rounded divisor rows of ROUNDED_CLASS_CORE_PROOF.  Order as the archive generator."""
    h, y, F, ori, q, z = key
    t = 5 if ori == "M" else 7
    C = 4 * t
    x = G - 32 - h - y
    qe = q_eff_of(key)
    def vec(fn): return [fn(r, u, v) for r, u, v in types]
    # ---- budgets (name, s, g(n) as a vector, b): s*p - g(n) <= b
    budgets = [("fixed repeated-color capacity", 1, [0] * len(types), qe)]          # B1: p <= q_eff
    if ori == "Mt":
        h0 = vec(lambda r, u, v: int(r == 0))
        h00 = vec(lambda r, u, v: int(r == 0 and u == 0))
        V0_minus_h00 = vec(lambda r, u, v: (v - int(u == 0)) if r == 0 else 0)           # V0 - h00, V0 = sum_{r=0} v n
        D2 = vec(lambda r, u, v: ((2 * v - 2) if u == 0 else (v + min(v, q - u))) if r == 0 else 0)   # 2V00 + V+ + M+ - 2h00
        budgets += [("unanchored helper capacity", 1, h0, q - 1),                      # B2: p - h0 <= q - 1       (EE_QUOTIENT (7b))
                    ("HH unanchored incidence deficiency", 3, V0_minus_h00, 3 * (q - 1)),   # B3: 3p - (V0 - h00) <= 3(q-1)  ((T) + (N))
                    ("HH edge deficiency", 3, [-c for c in h00], 3 * (q - 1) + z),     # B4: 3p + h00 <= 3(q-1) + z   ((T) + (N))
                    ("HH label matching deficiency", 6, D2, 6 * (q - 1))]              # B5: 6p - D2 <= 6(q-1)      (matching (M))
        if q <= 6 or y <= 3:
            W2 = vec(lambda r, u, v: 2 * int(r == 0) + (v if r in (1, 2) else 0))      # 2 h0 + W, W = sum_{r=1,2} v n
            budgets.append(("small palette anchored full HH", 1, W2, q - 2))          # B6: p - 2h0 - W <= q - 2  (F5c)
    # ---- resources (name, K(n), base, c): K(n) <= base + c*p
    U = vec(lambda r, u, v: u if r >= 2 else 0)                       # U_rep: missing incidences at repeated helpers
    Erep = vec(lambda r, u, v: max(0, r - 1))                         # E_rep = N2 + 2 N3
    Cost = vec(lambda r, u, v: int(r == 2) + 5 * int(r == 3))         # N2 + 5 N3
    A = vec(lambda r, u, v: u if r == 3 else 0)
    Q = vec(lambda r, u, v: max(0, r - 1) * u + (max(0, u - 2) if r == 3 else 0))   # Z + E
    resources = [("repeated contact core ownership", [a + b for a, b in zip(Erep, U)], C, 1),          # R1: E_rep + U_rep <= C + p
                 ("repeated contact OO three halves", [2 * a + 3 * b for a, b in zip(Cost, U)], 2 * x + 2 * C, 3),  # R2
                 ("repeated contact OO full colors", [a + 2 * b + c for a, b, c in zip(Cost, U, A)], x + C, 3)]     # R3
    if ori == "Mt":
        resources += [("full contacts", A, 0, 1),                      # R4: A <= p   (one full contact per label)
                      ("weighted excess", Q, 0, 3)]                    # R5: Z + E <= 3p
    for ratio in overload_ratios(q):                                  # R6: sum_{r>=2} floor(a(r-1+u)/d) n <= t floor(4a/d) + p
        a, d = ratio.numerator, ratio.denominator
        resources.append(("class overload ratio %d/%d" % (a, d), vec(lambda r, u, v, a=a, d=d: (a * (r - 1 + u)) // d if r >= 2 else 0), t * ((4 * a) // d), 1))
    new = {}
    order = []
    def add(name, row, bound):
        common = gcd(abs(bound), *(abs(c) for c in row))
        if common > 1:
            row = [c // common for c in row]; bound //= common
        if not any(row) and bound >= 0: return
        sig = tuple(row)
        if not dedup:
            order.append((sig, bound, "push6 " + name + " <=")); return
        if sig not in new:
            order.append(sig)
        if sig not in new or bound < new[sig][0]:
            new[sig] = (bound, "push6 " + name + " <=")
    for rname, K, base, c in resources:
        for bname, s, g, b in budgets:
            add(rname + " / " + bname, [s * k - c * gg for k, gg in zip(K, g)], s * base + c * b)
    for d in range(2, q + 3):                                         # divisor rows: constant q_eff inside the floors
        cap = min((t * ((4 * k + qe) // d)) // k for k in range(1, t + 1))
        add("rounded class core divisor %d" % d, vec(lambda r, u, v, d=d: (r - 1 + u) // d if r >= 2 else 0), cap)
    if not dedup:
        return [(nm, list(sig), b) for sig, b, nm in order]
    return [(new[sig][1], list(sig), new[sig][0]) for sig in order]


def push_rows(key, types, G=G, dedup=True):
    return push5_rows(key, types, G) + push6_rows(key, types, G, dedup)


# ----------------------------------------------------------------------------------------------- the combined case matrix
PUSHCACHE = {}
def push_block(key):
    if key not in PUSHCACHE:
        types0 = package_types(key)
        PUSHCACHE[key] = (types0, push_rows(key, types0))
    return PUSHCACHE[key]


def matrix(key, hub, dark):
    """(b, [(label, column)], n_sprint, names_push, (n_pkg, n_b1, n_flat)): sprint case system (check_cases4.matrix) then the
    push rows restricted to the kept type columns, zero on the auxiliary columns y0, y1, y2 (, y2d, Fb, Fd)."""
    b, cols, n_pkg, n_b1, n_flat = c4.matrix(key, hub, dark)
    n_sprint = len(b)
    types0, prow = push_block(key)
    idx = {tp: j for j, tp in enumerate(types0)}
    out = []
    for lab, col in cols:
        if isinstance(lab, tuple):
            assert lab in idx, ("a case column outside the package type list", key, hub, dark, lab)
            out.append((lab, list(col) + [coef[idx[lab]] for _, coef, _ in prow]))
        else:
            out.append((lab, list(col) + [0] * len(prow)))
    b2 = list(b) + [bb for _, _, bb in prow]
    for lab, col in out: assert len(col) == len(b2)
    return b2, out, n_sprint, [nm for nm, _, _ in prow], (n_pkg, n_b1, n_flat)


def check_weights(weights, b, cols):
    assert isinstance(weights, list) and all(type(w) is int and w >= 0 for w in weights), "weights must be nonnegative integers"
    assert len(weights) == len(b), ("length", len(weights), len(b))
    wrhs = sum(w * bi for w, bi in zip(weights, b))
    assert wrhs <= -1, ("weighted right-hand side not <= -1", wrhs)
    for lab, col in cols:
        s = sum(w * c for w, c in zip(weights, col))
        assert s >= 0, ("negative column coefficient", lab, s)
    return len(cols), wrhs


def legal_case(key, hub, dark):
    q = key[4]
    if hub is not None and not (isinstance(hub, (list, tuple)) and len(hub) == 2 and hub[0] == "eq" and type(hub[1]) is int and 0 <= hub[1] <= q): return False
    if dark is not None and not (type(dark) is int and 0 <= dark <= q): return False
    return True


def check_certificate(key, hub, dark, weights):
    h, y, F, ori, q, z = key
    assert ori in ("M", "Mt") and all(type(v) is int and v >= 0 for v in (h, y, F, q, z))
    assert legal_case(key, hub, dark), ("illegal case", key, hub, dark)
    b, cols, n_sprint, pnames, (n_pkg, n_b1, n_flat) = matrix(key, hub, dark)
    count, wrhs = check_weights(weights, b, cols)
    used_push = [pnames[i] for i in range(len(pnames)) if weights[n_sprint + i]]
    uses_lim = hub is not None and bool(weights[n_sprint - 1])      # LIM is the last joint row of a hub case
    uses_joint = hub is not None and any(weights[n_sprint - NJ:n_sprint])
    return dict(count=count, wrhs=wrhs, n_sprint=n_sprint, n_pkg=n_pkg, n_b1=n_b1, n_flat=n_flat, nrows=len(b),
                used_push=used_push, uses_lim=uses_lim, uses_joint=uses_joint)


# ----------------------------------------------------------------------------------------------- coverage (own code)
def c2(x): return x * (x - 1) // 2


def least_s(h, y):
    for s in range(65):
        if any(2 * h + y + (s - q) + c2(q) >= 32 for q in range(s + 1)): return s
    raise AssertionError


def scalar_states(G=G):
    states = set()
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
                    le, lo = least_s(he, Y), least_s(ho, V)
                    budget = a + b + 2 * G - 192
                    if le <= Se and lo <= So and le + lo <= budget:
                        states.add((a, b, Y, V, he, ho, le, lo, Se, So, budget))
    return states


def direct_exclusion(key):
    _, _, _, ori, q, z = key
    return (q == 0 and z == 0) or (ori == "Mt" and q == 0 and z < 8)


def leaves(q): return [(("eq", a), d) for a in range(q + 1) for d in range(q + 1)]


def covered(cases, q):
    if (None, None) in cases: return True
    for hc, d in leaves(q):
        if (hc, None) in cases or (None, d) in cases or (hc, d) in cases: continue
        return False
    return True


def claim_keys(state, ori, k, l):
    """the keys a claim (state, ori, k, l) references: every (q, z) below the stated bound on each phase that passes the
    incidence test and is not directly excluded; returns (keys, direct_count)."""
    a, b, Y, V, ha, hb, la, lb, Sa, Sb, budget = state
    other = "Mt" if ori == "M" else "M"
    keys = []; direct = 0
    for h, y, F, o, low, cap, bound in ((ha, Y, V, ori, la, Sa, k), (hb, V, Y, other, lb, Sb, l)):
        for total in range(low, min(cap, bound - 1) + 1):
            for z in range(total + 1):
                q = total - z
                if 2 * h + y + z + c2(q) < 32: continue
                key = (h, y, F, o, q, z)
                if direct_exclusion(key): direct += 1; continue
                keys.append(key)
    return keys, direct


def claims_check(claims, certs, states):
    """claims: [(state, ori, k, l)]; certs: {key: set of (hub, dark)}.  Returns (references, direct, distinct keys) or raises."""
    seen = set(); references = 0; direct = 0; distinct = set()
    for st, ori, k, l in claims:
        st = tuple(st)
        assert st in states, ("state outside the admissible domain", st)
        assert (st, ori) not in seen, ("duplicate claim", st, ori); seen.add((st, ori))
        a, b, Y, V, ha, hb, la, lb, Sa, Sb, budget = st
        assert type(k) is int and type(l) is int and la <= k <= Sa + 1 and lb <= l <= Sb + 1, (st, ori, k, l)
        keys, d = claim_keys(st, ori, k, l); direct += d
        for key in keys:
            assert key in certs, ("uncovered key", (st, ori), key)
            assert covered(certs[key], key[4]), ("referenced key not covered in every case", (st, ori), key)
            references += 1; distinct.add(key)
        assert k > Sa or l > Sb or k + l > budget, ("final test fails", st, ori, k, l)
    return references, direct, distinct


# ----------------------------------------------------------------------------------------------- verification
def verify(data, addendum, quiet=False):
    t0 = time.time()
    assert data["gates"] == G
    states = scalar_states()
    assert states == c3.scalar_domain(), "own scalar domain differs from check_cases3_copy.scalar_domain"
    certs = {}; kinds = Counter(); coefficients = 0; rhs = []; push_fam = Counter(); push_rows_used = Counter()
    n_push_certs = 0; n_lim = 0; n_joint = 0; keys_push = set(); keys_lim = set(); lim_certs = []
    hub_hist = Counter(); dark_hist = Counter(); case_kinds = Counter(); rows_total = 0
    for e in data["certificates"]:
        key = tuple(e["key"]); hub = tuple(e["hub"]) if e.get("hub") is not None else None; dark = e.get("qD")
        assert e.get("A") == (hub[1] if hub else None), ("A field disagrees with hub", key, hub)
        r = check_certificate(key, hub, dark, e["weights"])
        kind = e["kind"]; w = e["weights"]; ns = r["n_sprint"]; n_pkg, n_b1, n_flat = r["n_pkg"], r["n_b1"], r["n_flat"]
        uses_push = bool(r["used_push"])
        assert uses_push == bool(e.get("uses_push")), ("uses_push field wrong", key, hub, dark)
        assert r["uses_lim"] == bool(e.get("uses_LIM")), ("uses_LIM field wrong", key, hub, dark)
        assert r["uses_joint"] == bool(e.get("uses_joint")), ("uses_joint field wrong", key, hub, dark)
        if kind == "package":
            assert hub is None and dark is None and not any(w[n_pkg:]), ("package certificate uses other rows", key)
        elif kind == "batch1":
            assert hub is None and dark is None and any(w[n_pkg:n_pkg + n_b1]) and not any(w[n_pkg + n_b1:]), ("batch1 certificate misuses rows", key)
        elif kind == "flat":
            assert hub is None and dark is None and any(w[n_pkg + n_b1:n_pkg + n_b1 + n_flat]) and not uses_push, ("flat certificate misuses rows", key)
        elif kind == "push":
            assert hub is None and dark is None and uses_push, ("push certificate without a push row or with a case", key)
        elif kind == "case":
            assert hub is not None or dark is not None, ("case certificate without a case", key)
            case_kinds["hub+dark" if (hub is not None and dark is not None) else ("hub-only" if hub is not None else "dark-only")] += 1
            if hub is not None: hub_hist[hub[1]] += 1
            if dark is not None: dark_hist[dark] += 1
        else:
            raise AssertionError(("unknown kind", key, kind))
        kinds[kind] += 1
        cs = certs.setdefault(key, set())
        assert (hub, dark) not in cs, ("duplicate certificate", key, hub, dark)
        cs.add((hub, dark))
        coefficients += r["count"]; rhs.append(r["wrhs"]); rows_total += r["nrows"]
        if uses_push:
            n_push_certs += 1; keys_push.add(key)
            for nm in r["used_push"]:
                push_rows_used[nm] += 1
                fam = nm.replace(" <=", "")
                if fam.startswith("push6 class overload ratio"): fam = "push6 class overload ratio a/d / " + fam.split(" / ")[1]
                elif fam.startswith("push6 rounded class core divisor"): fam = "push6 rounded class core divisor d"
                push_fam[fam] += 1
        if r["uses_lim"]: n_lim += 1; keys_lim.add(key); lim_certs.append((key, hub, dark))
        if r["uses_joint"]: n_joint += 1
    # ---- coverage of the excluded claims
    claims = [(tuple(st), o, k, l) for st, o, k, l in data["claims_excluded"]]
    references, direct, distinct = claims_check(claims, certs, states)
    assert distinct == set(certs), ("certified keys differ from referenced keys", len(distinct), len(certs))
    keys_covered = {k for k, cs in certs.items() if covered(cs, k[4])}
    assert keys_covered == set(certs), "some certified key is not covered in every case"
    # ---- what holds without row LIM (finite fact J1): drop the LIM-using certificates
    limset = set(lim_certs)
    certs_free = {k: {c for c in cs if (k, c[0], c[1]) not in limset} for k, cs in certs.items()}
    claims_fail_free = []
    for cl in claims:
        try: claims_check([cl], certs_free, states)
        except AssertionError: claims_fail_free.append(cl)
    # ---- the J1-free addendum: certificates re-covering the claims that touched LIM, with the no-LIM scan's bounds
    add_certs = {}; add_coef = 0; add_rhs = []; add_kinds = Counter()
    for e in addendum["certificates"]:
        key = tuple(e["key"]); hub = tuple(e["hub"]) if e.get("hub") is not None else None; dark = e.get("qD")
        r = check_certificate(key, hub, dark, e["weights"])
        assert not r["uses_lim"], ("addendum certificate uses LIM", key, hub, dark)
        add_kinds[e["kind"]] += 1
        cs = add_certs.setdefault(key, set()); assert (hub, dark) not in cs; cs.add((hub, dark))
        add_coef += r["count"]; add_rhs.append(r["wrhs"])
    add_claims = [(tuple(st), o, k, l) for st, o, k, l in addendum["claims"]]
    assert {(st, o) for st, o, k, l in add_claims} == {(st, o) for st, o, k, l in claims_fail_free}, "addendum claims differ from the claims that touch LIM"
    main_bounds = {(st, o): (k, l) for st, o, k, l in claims}
    add_refs_alone, add_direct, add_distinct = claims_check(add_claims, add_certs, states)   # the addendum alone covers its claims
    merged = {k: set(v) for k, v in certs_free.items()}
    for k, v in add_certs.items(): merged.setdefault(k, set()).update(v)
    claims_check(add_claims, merged, states)
    bounds_differ = sum(1 for st, o, k, l in add_claims if main_bounds[(st, o)] != (k, l))
    result = dict(gates=G, scalar_states=len(states), claims_checked=len(claims), claims_M=sum(1 for st, o, k, l in claims if o == "M"),
                  certificates=sum(kinds.values()), certificates_by_kind=dict(kinds), case_certificates=dict(case_kinds),
                  hub_case_histogram={str(k): v for k, v in sorted(hub_hist.items())}, dark_case_histogram={str(k): v for k, v in sorted(dark_hist.items())},
                  certificates_using_push_rows=n_push_certs, certificates_using_LIM=n_lim, certificates_using_joint_rows=n_joint,
                  keys_with_certificates=len(certs), keys_with_push_certificate=len(keys_push), keys_with_LIM_certificate=len(keys_lim),
                  lim_certificates=[[list(k), list(h) if h else None, d] for k, h, d in lim_certs],
                  certificate_references=references, direct_exclusion_references=direct, distinct_referenced_keys=len(distinct),
                  coefficients_checked=coefficients, rows_checked=rows_total, largest_weighted_rhs=max(rhs),
                  claims_not_covered_without_LIM=len(claims_fail_free),
                  push_row_families_used=dict(push_fam.most_common()), distinct_push_rows_used=len(push_rows_used),
                  addendum_certificates=sum(add_kinds.values()), addendum_by_kind=dict(add_kinds), addendum_keys=len(add_certs),
                  addendum_claims=len(add_claims), addendum_references=add_refs_alone, addendum_direct=add_direct,
                  addendum_claims_with_different_bounds=bounds_differ, addendum_coefficients=add_coef, addendum_largest_weighted_rhs=max(add_rhs),
                  seconds=round(time.time() - t0, 1), all_checks_passed=True)
    if not quiet: print(json.dumps(result, indent=1))
    return result


EXPECTED = {"scalar_states": 3708, "claims_checked": 406, "claims_M": 224, "certificates": 4653,
            "certificates_by_kind": {"package": 2565, "push": 645, "case": 879, "batch1": 561, "flat": 3},
            "case_certificates": {"hub-only": 535, "hub+dark": 344}, "certificates_using_push_rows": 1247, "certificates_using_LIM": 1,
            "certificates_using_joint_rows": 113, "keys_with_certificates": 3863, "keys_with_push_certificate": 734, "keys_with_LIM_certificate": 1,
            "certificate_references": 8207, "direct_exclusion_references": 1288, "distinct_referenced_keys": 3863,
            "coefficients_checked": 188062, "rows_checked": 371485, "largest_weighted_rhs": -1, "claims_not_covered_without_LIM": 4,
            "distinct_push_rows_used": 26, "addendum_certificates": 43, "addendum_by_kind": {"batch1": 17, "package": 13, "flat": 13},
            "addendum_keys": 43, "addendum_claims": 4, "addendum_references": 67, "addendum_direct": 13,
            "addendum_claims_with_different_bounds": 4, "addendum_coefficients": 1626, "addendum_largest_weighted_rhs": -1}
# pinned 2026-11-09 from the first run of this checker (check_run1.out); the push-row family counts are compared in REPORT.md

if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else RECON / "CERTIFICATES_COMBINED75.json"
    src2 = Path(sys.argv[2]) if len(sys.argv) > 2 else RECON / "CERTIFICATES_COMBINED75_J1FREE_ADDENDUM.json"
    data = json.loads(src.read_text()); addendum = json.loads(src2.read_text())
    res = verify(data, addendum)
    exp = json.loads(sys.argv[3]) if len(sys.argv) > 3 else EXPECTED
    for k, v in exp.items():
        assert res[k] == v, ("expected", k, v, "got", res[k])
    if exp: print("expected counts match:", json.dumps(exp))
    Path(__file__).with_name("CHECKED_COMBINED75.json").write_text(json.dumps(res, indent=1) + "\n")
    print("INDEPENDENT CHECK PASSED")
