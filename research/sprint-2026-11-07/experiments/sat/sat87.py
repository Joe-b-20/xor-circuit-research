"""Scoped exact search for an 87-gate AES MixColumns circuit.

Formulation (value-set form).
  A circuit is a set V of 32-bit masks (bit j = x_j) such that every v in V is the XOR of two
  distinct elements of (INPUTS u V) that come earlier in some order ("split-closed").  Its cost
  is |V|.  V must contain the 32 targets.  An 88 circuit S has |S| = 88.

  Scope: a subset K of S (the kept values) with INPUTS u K split-closed.  Instance I(K, m):
  do there exist m new values g_1..g_m with g_j = XOR of two distinct elements of
  P_j = INPUTS u K u {g_1..g_{j-1}} such that every target not in K is some g_j ?
  Claim [proved]: I(K, m) is SAT  <=>  there is a split-closed V, V >= K u TARGETS, |V| <= |K| + m.
    (=>) V = K u {g_j}.  (<=) order V so that K comes first (possible: INPUTS u K is split-closed
    by itself), the remaining <= m values each split over earlier ones; pad with duplicates (a
    duplicate g_j = some earlier value is allowed by the encoding, no distinctness is required).
  So UNSAT of I(K, |S| - |K| - 1) proves: no circuit with <= 87 gates has a value set containing K.
  That is a statement about the MAP restricted to circuits through K; it says nothing about
  circuits that drop any value of K.

Encoding (per instance, pysat CNF):
  pool index u = 0..31 inputs, 32..32+|K|-1 kept values (constants), then new gates (variables).
  For new gate j (pool index w_j):
    a[j][u], b[j][u]  one-hot selectors (exactly-one via pairwise + at-least-one), u < w_j
    c[j][u] = OR_{u' <= u} a[j][u'] (prefix), and b[j][u] -> c[j][u-1]: first operand index <
      second operand index (kills the operand swap symmetry; sound).
    bit i of operand A: A_i <-> OR_{u: const bit set} a[j][u]  OR  OR_{u new} (a[j][u] & bit[u][i])
      (exactly-one selector makes this exact); same for B; bit[j][i] = A_i xor B_i.
    optional distinctness: for each earlier pool element u, some bit of g_j differs from u.
    symmetry between consecutive new gates [sound by bubble-sort argument]: if g_{j+1} does not
      use g_j (b[j+1][w_j] false; g_j can only be the second operand because it has the largest
      index) then first operand index of g_j <= first operand index of g_{j+1}:
      clause (b[j+1][w_j] or -c[j+1][u] or c[j][u]) for all u.
  Targets: for each target t not in K, OR_j e[j][t] with e[j][t] -> bit[j][i] == t_i for all i.
"""
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.expanduser("~/xor-circuit-research")
MAT = os.path.join(REPO, "circuits/aes-mixcolumns/aes-mixcolumns.mat.txt")
REPO88 = os.path.join(REPO, "circuits/aes-mixcolumns/aes-mixcolumns-xor88-depth5.circ.txt")
SPRINT = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint")
N = 32
INPUTS = [1 << j for j in range(N)]


def load_targets():
    toks = " ".join(l.split("%")[0] for l in open(MAT).read().splitlines()).split()
    r, c = int(toks[1]), int(toks[2])
    bits = list(map(int, toks[3:3 + r * c]))
    return [sum(bits[i * c + j] << j for j in range(c)) for i in range(r)]


TARGETS = load_targets()
TSET = set(TARGETS)
assert len(TSET) == 32


def rot(v, s):
    """Byte rotation of a mask by s bytes (Z4 symmetry of the map)."""
    s = (s * 8) % 32
    return ((v << s) | (v >> (32 - s))) & 0xFFFFFFFF


# ------------------------------------------------------------------ circuit loading
def wiring_from_values(values):
    """Topological wiring for a value set: list of (v, a, b) with a ^ b = v, a, b earlier or
    inputs.  Greedy closure: any pair in the available set.  Returns None if not closed."""
    avail = set(INPUTS)
    todo = set(values) - avail
    order = []
    while todo:
        found = None
        al = sorted(avail)
        aset = avail
        for v in sorted(todo):
            for a in al:
                b = a ^ v
                if b in aset and b != a:
                    found = (v, a, b)
                    break
            if found:
                break
        if not found:
            return None
        order.append(found)
        avail.add(found[0])
        todo.discard(found[0])
    return order


def load_repo_circ(path=REPO88):
    vals = {f"x{j}": 1 << j for j in range(N)}
    order = []
    for line in open(path):
        m = re.match(r"^XOR\s+(\S+)\s+(\S+)\s+(\S+)", line.strip())
        if not m:
            continue
        o, a, b = m.groups()
        vals[o] = vals[a] ^ vals[b]
        order.append((vals[o], vals[a], vals[b]))
    return order


def load_record(path):
    d = json.load(open(path))
    wire = list(INPUTS)
    order = []
    for a, b in d["gates"]:
        v = wire[a] ^ wire[b]
        order.append((v, wire[a], wire[b]))
        wire.append(v)
    return order


def load_samples(path, gates=88):
    out = []
    for i, line in enumerate(open(path)):
        d = json.loads(line)
        if d.get("gates") != gates:
            continue
        out.append((i, d))
    return out


def values_of(order):
    return [v for v, _, _ in order]


def check_circuit(order):
    """Independent check of a wiring list: every gate splits over earlier values, all 32
    targets present, count and depth.  Returns (gates, depth, n_distinct)."""
    avail = {v: 0 for v in INPUTS}
    for v, a, b in order:
        assert a in avail and b in avail and a != b and a ^ b == v, "bad gate"
        avail[v] = 1 + max(avail[a], avail[b])
    for t in TARGETS:
        assert t in avail, "target missing"
    depth = max(avail[t] for t in TARGETS)
    return len(order), depth, len(set(values_of(order)))


# ------------------------------------------------------------------ closure
def split_closed(K):
    """Is INPUTS u K split-closed (each v in K = a ^ b for earlier a, b)?  Returns the set of
    computable values (== K if closed)."""
    return set(values_of(wiring_from_values(K) or [])) == set(K)


def dependents(order):
    """Under the given wiring: users[v] = set of values using v as operand."""
    users = {v: set() for v, _, _ in order}
    for v, a, b in order:
        for o in (a, b):
            if o in users:
                users[o].add(v)
    return users


def closure_remove(order, W):
    """Remove W and everything (under the wiring) that depends on it: returns the removed set."""
    users = dependents(order)
    rem = set(W)
    stack = list(W)
    while stack:
        v = stack.pop()
        for u in users.get(v, ()):
            if u not in rem:
                rem.add(u)
                stack.append(u)
    return rem


def private_cone(order, roots, extra_removed=()):
    """Values that would become dead if `roots` were removed: the roots plus every value all of
    whose users are (recursively) removed and which is not a target."""
    users = dependents(order)
    rem = set(roots) | set(extra_removed)
    changed = True
    while changed:
        changed = False
        for v, _, _ in order:
            if v in rem or v in TSET:
                continue
            if users[v] and users[v] <= rem:
                rem.add(v)
                changed = True
    return rem


# ------------------------------------------------------------------ encoding
def encode(K, m, distinct=True, symbreak=True):
    """Build clauses for I(K, m).  Returns (clauses, nvars, meta) where meta lets us decode."""
    K = sorted(K)
    const = INPUTS + K                      # pool constants
    nc = len(const)
    need = [t for t in TARGETS if t not in set(K)]
    nv = [0]

    def new():
        nv[0] += 1
        return nv[0]

    cl = []
    bit = []            # bit[j][i] variable of new gate j
    A = []              # selectors
    B = []
    C = []              # prefix of A
    for j in range(m):
        w = nc + j
        a = [new() for _ in range(w)]
        b = [new() for _ in range(w)]
        c = [new() for _ in range(w)]
        A.append(a); B.append(b); C.append(c)
        for sel in (a, b):
            cl.append(sel[:])
            for x in range(w):
                for y in range(x + 1, w):
                    cl.append([-sel[x], -sel[y]])
        # prefix c[u] <-> a[0] or ... or a[u]
        cl.append([-c[0], a[0]]); cl.append([c[0], -a[0]])
        for u in range(1, w):
            cl.append([-c[u], c[u - 1], a[u]])
            cl.append([c[u], -c[u - 1]])
            cl.append([c[u], -a[u]])
        # first operand strictly before second
        cl.append([-b[0]])
        for u in range(1, w):
            cl.append([-b[u], c[u - 1]])
        g = [new() for _ in range(N)]
        bit.append(g)
        for i in range(N):
            # Ai: operand A bit i
            Ai, Bi = new(), new()
            for sel, X in ((a, Ai), (b, Bi)):
                terms = []
                for u in range(w):
                    if u < nc:
                        if (const[u] >> i) & 1:
                            terms.append(sel[u])
                    else:
                        t = new()
                        bu = bit[u - nc][i]
                        cl += [[-t, sel[u]], [-t, bu], [t, -sel[u], -bu]]
                        terms.append(t)
                # X <-> OR(terms)   (at most one term true by exactly-one)
                cl.append([-X] + terms)
                for t in terms:
                    cl.append([X, -t])
            # g = Ai xor Bi
            cl += [[-g[i], Ai, Bi], [-g[i], -Ai, -Bi], [g[i], -Ai, Bi], [g[i], Ai, -Bi]]
        if distinct:
            for u in range(w):
                if u < nc:
                    v = const[u]
                    cl.append([(-g[i] if (v >> i) & 1 else g[i]) for i in range(N)])
                else:
                    diff = []
                    for i in range(N):
                        d = new()
                        bu = bit[u - nc][i]
                        cl += [[-d, g[i], bu], [-d, -g[i], -bu]]
                        diff.append(d)
                    cl.append(diff)
        if symbreak and j > 0:
            wprev = nc + j - 1
            for u in range(wprev):
                cl.append([b[wprev], -c[u], C[j - 1][u]])
    # targets
    for t in need:
        es = []
        for j in range(m):
            e = new()
            for i in range(N):
                cl.append([-e, bit[j][i] if (t >> i) & 1 else -bit[j][i]])
            es.append(e)
        cl.append(es)
    meta = {"K": K, "m": m, "A": A, "B": B, "bit": bit, "const": const}
    return cl, nv[0], meta


def decode(model, meta):
    ms = set(x for x in model if x > 0)
    const = meta["const"]
    vals = list(const)
    order = []
    for j in range(meta["m"]):
        a = [u for u in range(len(meta["A"][j])) if meta["A"][j][u] in ms]
        b = [u for u in range(len(meta["B"][j])) if meta["B"][j][u] in ms]
        assert len(a) == 1 and len(b) == 1
        va, vb = vals[a[0]], vals[b[0]]
        v = sum(1 << i for i in range(N) if meta["bit"][j][i] in ms)
        assert v == va ^ vb
        order.append((v, va, vb))
        vals.append(v)
    return order


# ------------------------------------------------------------------ solving (child process)
def solve_instance(K, m, limit, solver="cadical195", distinct=True, symbreak=True, tag=""):
    """Run one instance in a child process under nice 10 with a hard wall limit.
    Returns dict(result in {SAT, UNSAT, TIMEOUT}, secs, nvars, nclauses, new_gates or None)."""
    req = {"K": sorted(K), "m": m, "solver": solver, "distinct": distinct, "symbreak": symbreak}
    tmp = os.path.join(HERE, "tmp_req.json")
    json.dump(req, open(tmp, "w"))
    t0 = time.time()
    try:
        p = subprocess.run(["nice", "-n", "10", "python3", os.path.join(HERE, "solve_child.py"), tmp],
                           capture_output=True, text=True, timeout=limit + 5)
        out = p.stdout.strip().splitlines()
        res = json.loads(out[-1]) if out else {"result": "ERROR", "err": p.stderr[-500:]}
    except subprocess.TimeoutExpired:
        res = {"result": "TIMEOUT"}
    res["secs"] = round(time.time() - t0, 1)
    res["limit"] = limit
    res["tag"] = tag
    return res


def wiring_from_values_partial(values):
    """Like wiring_from_values but returns the computable prefix instead of None."""
    avail = set(INPUTS)
    todo = set(values) - avail
    order = []
    while todo:
        found = None
        al = sorted(avail)
        for v in sorted(todo):
            for a in al:
                b = a ^ v
                if b in avail and b != a:
                    found = (v, a, b)
                    break
            if found:
                break
        if not found:
            break
        order.append(found)
        avail.add(found[0])
        todo.discard(found[0])
    return order
