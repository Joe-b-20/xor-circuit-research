#!/usr/bin/env python3
"""Skeleton transformations for depth (track F): distribute ANDs over XOR splits of their
operands, AND(L1^L2, R1^R2) = sum AND(Li, Rj), reusing existing products, and measure the
skeleton depth bound (Huffman/Kraft over arrival levels) after each.

Skeleton: inputs x0..x7, ANDs k = (L_k, R_k) as affine forms (Python int over basis
0 = const, 1..8 = inputs, 9.. = ANDs), outputs as forms.  Forms are kept over the basis, so a
substitution of AND k by a sum of products is a basis change: every form containing bit k gets
the replacement's bits XORed in.

    python3 skelxf.py FILE --cap D   # single and greedy multi transforms, bound after each
"""
import heapq
import itertools
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2])); sys.path.insert(0, str(HERE))
from boolflux import core, skeleton   # noqa: E402
from skeldepth import huff   # noqa: E402

N = 8


def bits(f):
    out = []; p = 0
    while f:
        if f & 1: out.append(p)
        f >>= 1; p += 1
    return out


class Skel:
    """ANDs list of (L, R) forms with basis index 1+N+k; supports appending ANDs and deleting
    (substituting) ANDs.  Deleted ANDs stay as None entries so indices are stable."""
    def __init__(self, ands, outs):
        self.ands = list(ands); self.outs = list(outs)

    @classmethod
    def from_circuit(cls, c):
        sk = skeleton.extract(c)
        return cls(sk['ands'], sk['outputs'])

    def copy(self):
        return Skel(self.ands, self.outs)

    def nand(self):
        return sum(1 for a in self.ands if a is not None)

    def order(self):
        """Topological order of live ANDs (an AND depends on the ANDs in its forms)."""
        K = len(self.ands); state = [0] * K; out = []
        for r in range(K):
            if self.ands[r] is None or state[r]: continue
            stack = [r]
            while stack:
                k = stack[-1]
                if state[k] == 2: stack.pop(); continue
                state[k] = 1
                deps = [p - 1 - N for p in bits(self.ands[k][0] | self.ands[k][1]) if p > N]
                pend = [d for d in deps if state[d] == 0]
                if any(state[d] == 1 for d in deps): raise ValueError('cycle')
                if pend: stack += pend; continue
                state[k] = 2; out.append(k); stack.pop()
        return out

    def arrivals(self):
        arr = {p: 0 for p in range(1, N + 1)}
        for k in self.order():
            L, R = self.ands[k]
            def d(f):
                t = [p for p in bits(f) if p > 0]
                return huff([arr[p] for p in t], bool(f & 1))
            arr[1 + N + k] = 1 + max(d(L), d(R))
        return arr

    def bound(self):
        arr = self.arrivals()
        ol = [huff([arr[p] for p in bits(f) if p > 0], bool(f & 1)) for f in self.outs]
        return max(ol), ol, arr

    def find_and(self, L, R):
        for k, a in enumerate(self.ands):
            if a is None: continue
            if (a[0] == L and a[1] == R) or (a[0] == R and a[1] == L): return k
        return None

    def substitute(self, k, repl):
        """Replace basis element of AND k by the form repl everywhere; delete AND k."""
        bit = 1 << (1 + N + k)
        self.ands[k] = None
        for j, a in enumerate(self.ands):
            if a is None: continue
            L, R = a
            if L & bit: L ^= bit ^ repl
            if R & bit: R ^= bit ^ repl
            self.ands[j] = (L, R)
        self.outs = [(f ^ bit ^ repl) if f & bit else f for f in self.outs]

    def distribute(self, k, Ls, Rs):
        """AND k = (L, R) with L = xor(Ls), R = xor(Rs): replace by sum of AND(Li, Rj).
        Returns number of ANDs added (net)."""
        added = 0; repl = 0
        for Li in Ls:
            for Rj in Rs:
                if Li == 0 or Rj == 0: continue
                if Li == 1: repl ^= Rj; continue          # AND(1, R) = R
                if Rj == 1: repl ^= Li; continue
                j = self.find_and(Li, Rj)
                if j is None or j == k:
                    self.ands.append((Li, Rj)); j = len(self.ands) - 1; added += 1
                repl ^= 1 << (1 + N + j)
        self.substitute(k, repl)
        return added - 1


def gate_forms(c):
    """Form of every signal of c over the skeleton basis (as skeleton.extract)."""
    form = [1 << (1 + i) for i in range(c.n)]; na = 0; ops = []
    for op, a, b in c.gates:
        fa, fb = form[a], form[b]
        if op == 6: f = fa ^ fb
        elif op == 9: f = fa ^ fb ^ 1
        elif op == 3: f = fa ^ 1
        else:
            f = 1 << (1 + c.n + na); na += 1
        form.append(f); ops.append((op, a, b))
    return form


def splits(c, form, f):
    """Two-way splits of form f suggested by c's gates: if a gate computes f (up to constant)
    as XOR(u, v), split into (form u, form v ^ const)."""
    out = set()
    for j, (op, a, b) in enumerate(c.gates):
        s = c.n + j
        if op in (6, 9) and (form[s] | 1) == (f | 1):
            u = form[a]; v = f ^ u
            out.add(tuple(sorted((u, v))))
    return sorted(out)


if __name__ == '__main__':
    f = sys.argv[1]; D = int(sys.argv[sys.argv.index('--cap') + 1])
    c = core.read_ncff(f)
    sk = Skel.from_circuit(c); form = gate_forms(c)
    b0, ol0, arr0 = sk.bound()
    print('%s: %d ANDs, skeleton bound %d, outputs %s' % (Path(f).name, sk.nand(), b0, ol0))
    # single transforms on every AND, with operand splits from the circuit (one or both sides)
    res = []
    for k, (L, R) in enumerate(sk.ands):
        sl = [(L,)] + splits(c, form, L); sr = [(R,)] + splits(c, form, R)
        for Ls in sl:
            for Rs in sr:
                if len(Ls) == 1 and len(Rs) == 1: continue
                s2 = sk.copy()
                added = s2.distribute(k, list(Ls), list(Rs))
                b, ol, _ = s2.bound()
                kr = sum(sum(2.0 ** (_[p] - D) for p in bits(fo) if p > 0) for fo in s2.outs)
                res.append((b, sum(ol), added, k, len(Ls), len(Rs), arr0[1 + N + k]))
    res.sort()
    for r in res[:25]:
        print('  bound %d sum %d  +%d AND  AND%d (level %d) split %dx%d' % (r[0], r[1], r[2], r[3] + 1, r[6], r[4], r[5]))
