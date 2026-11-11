"""Reviewer's own SAT encoding of the local lemma (independent of free_prev.py / local_lemma.py).

Vector space F_2^8: bits 0..3 = block a (index c), bits 4..7 = block b (index c).
Base (free): every vector supported on a (including 0: harmless, only more permissive) and the
four units of b.  Gate k = w(k,0) XOR w(k,1); each operand w(k,p) is selected among
  FREE  : any vector with b-part 0 (its a-part is an unconstrained variable per operand),
  U_i   : unit i of b,
  G_i   : value of gate i < k.
No distinctness, no usefulness, no normalisation.  Targets T_c = [b: E_c] + [a: s_c] must each
equal some gate value.  Because duplicates / zero operands are allowed, a circuit with fewer than
K gates pads to exactly K (copy gate = U_0 + FREE(a-part of zero) ... any copy), so UNSAT at K
means no circuit with <= K gates.

Optional symmetry breaking (--sym), each justified in the comments below.
Usage: python3 lemma_sat.py K [--sym] [--solver cadical153]
"""
import sys
import time
from itertools import count
from pysat.solvers import Solver
from pysat.card import CardEnc, EncType

K = int(sys.argv[1])
SYM = "--sym" in sys.argv
solver_name = "cadical153"
if "--solver" in sys.argv:
    solver_name = sys.argv[sys.argv.index("--solver") + 1]

ctr = count(1)


def nv():
    return next(ctr)


def A(c):
    return 1 << (c % 4)


def B(c):
    return 1 << (4 + (c % 4))


targets = []
for c in range(4):
    E = B(c + 1) | B(c + 2) | B(c + 3)
    s = A(c) | A(c + 1)
    targets.append(E | s)
if "--targets" in sys.argv:  # cross-validation with other target sets
    targets = [int(x, 16) for x in sys.argv[sys.argv.index("--targets") + 1].split(",")]

clauses = []
v = [[nv() for _ in range(8)] for _ in range(K)]
w = [[[nv() for _ in range(8)] for _ in range(2)] for _ in range(K)]
sel = []  # sel[k][p] = dict name -> var
for k in range(K):
    sk = []
    for p in range(2):
        d = {"F": nv()}
        for i in range(4):
            d["U%d" % i] = nv()
        for i in range(k):
            d["G%d" % i] = nv()
        sk.append(d)
        clauses.append(list(d.values()))  # at least one choice
        # F -> b-part of operand zero
        for bit in range(4, 8):
            clauses.append([-d["F"], -w[k][p][bit]])
        for i in range(4):
            u = B(i)
            for bit in range(8):
                lit = w[k][p][bit] if (u >> bit) & 1 else -w[k][p][bit]
                clauses.append([-d["U%d" % i], lit])
        for i in range(k):
            g = d["G%d" % i]
            for bit in range(8):
                clauses.append([-g, -w[k][p][bit], v[i][bit]])
                clauses.append([-g, w[k][p][bit], -v[i][bit]])
    sel.append(sk)
    # v = w0 xor w1
    for bit in range(8):
        x, y, z = w[k][0][bit], w[k][1][bit], v[k][bit]
        clauses += [[-x, -y, -z], [x, y, -z], [x, -y, z], [-x, y, z]]

# targets
for t in targets:
    ys = []
    for k in range(K):
        yk = nv()
        ys.append(yk)
        for bit in range(8):
            clauses.append([-yk, v[k][bit] if (t >> bit) & 1 else -v[k][bit]])
    clauses.append(ys)

if SYM:
    # (S1) canonical topological order.  If gate k+1 does not use gate k as an operand, the two
    # gates can be swapped; repeatedly swapping adjacent pairs with v_{k+1} < v_k (lexicographic on
    # the 8 bits, bit 7 most significant) strictly reduces the number of value inversions, so every
    # circuit can be brought to a form in which: (k+1 uses k) or v_k <= v_{k+1}.  Targets are only
    # "some gate equals T", so they are unaffected.
    for k in range(K - 1):
        uses = [sel[k + 1][0]["G%d" % k], sel[k + 1][1]["G%d" % k]]
        # lex  v_k <= v_{k+1}  unless uses
        # eq_i : bits above i equal
        prev_eq = None
        for bit in range(7, -1, -1):
            a_, b_ = v[k][bit], v[k + 1][bit]
            # if all higher bits equal then not (a_=1 and b_=0)
            cl = [-a_, b_] + uses
            if prev_eq is not None:
                cl.append(-prev_eq)
            clauses.append(cl)
            # new eq var
            e = nv()
            # e -> (prev_eq and a_ == b_)
            if prev_eq is not None:
                clauses.append([-e, prev_eq])
            clauses.append([-e, -a_, b_])
            clauses.append([-e, a_, -b_])
            # (prev_eq and a_==b_) -> e
            base = [] if prev_eq is None else [-prev_eq]
            clauses.append(base + [e, a_, b_])
            clauses.append(base + [e, -a_, -b_])
            prev_eq = e
    # (S2) operand order: XOR is commutative, so swap the two operands of a gate if needed so that
    # the selector index of operand 0 is <= that of operand 1 (ordering F < U0..U3 < G0..).  Encoded
    # as: operand 1 may not select an option strictly before every option of operand 0 ... simpler:
    # forbid (operand0 = option j, operand1 = option i) for i < j.  Because 'at least one' choice is
    # used (not exactly one), we only forbid pairs, which is still sound: any circuit has an
    # ordering of its two operands with index(op0) <= index(op1) for the chosen options, and the
    # other selector variables can be set false.
    for k in range(K):
        names = list(sel[k][0].keys())
        for j, nj in enumerate(names):
            for i in range(j):
                ni = names[i]
                clauses.append([-sel[k][0][nj], -sel[k][1][ni]])

t0 = time.time()
with Solver(name=solver_name, bootstrap_with=clauses) as S:
    res = S.solve()
    dt = time.time() - t0
    print("K=%d sym=%s solver=%s vars=%d clauses=%d result=%s time=%.1fs"
          % (K, SYM, solver_name, next(ctr) - 1, len(clauses), "SAT" if res else "UNSAT", dt))
    if res:
        m = set(l for l in S.get_model() if l > 0)
        vals = []
        for k in range(K):
            val = sum(1 << bit for bit in range(8) if v[k][bit] in m)
            ops = []
            for p in range(2):
                ch = [n for n, var in sel[k][p].items() if var in m]
                wv = sum(1 << bit for bit in range(8) if w[k][p][bit] in m)
                ops.append((ch[0], wv))
            vals.append(val)
            print("gate %d = %s(%02x) + %s(%02x) -> %02x" % (k, ops[0][0], ops[0][1], ops[1][0], ops[1][1], val))
        # independent strict check: rebuild from base
        avail = set(range(16)) | {B(i) for i in range(4)}
        for k in range(K):
            ok = False
            for x in avail:
                if (x ^ vals[k]) in avail:
                    ok = True
                    break
            assert ok, "gate %d not computable" % k
            avail.add(vals[k])
        assert all(t in avail for t in targets)
        print("strict re-check OK; targets", [hex(t) for t in targets])
