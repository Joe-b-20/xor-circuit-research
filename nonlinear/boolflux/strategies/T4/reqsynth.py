#!/usr/bin/env python3
"""T4: required-time-driven synthesis of an AND skeleton with greedy reuse.
Every form F needed at level <= L is built as XOR(s, rest) where s is an already available signal
whose form is a subset of F with level <= L-1 and largest overlap, provided the rest can still be
built at <= L-1 (Huffman feasibility); otherwise Huffman over the terms.  Required levels come from
the skeleton depth bound (ANDs at their earliest level, outputs at CAP).  Optional parent circuit:
its gates are copied first and offered for reuse.
    python3 reqsynth.py SKEL.json OUT.circ.txt [PARENT.circ.txt] [CAP]"""
import sys, json, heapq
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core, targets, skeleton as SK  # noqa
from coversearch import bound, huff  # noqa

AND, XOR, XNOR, NOT = 8, 6, 9, 3


def synth(sk, n=8, parent=None, cap=11):
    b, arr, ol = bound(dict(sk, n=n, m=len(sk['outputs'])), n)
    gates = []; lvl = [0] * n
    pos_sig = {1 + i: i for i in range(n)}
    memo = {}                              # form (incl. const bit) -> signal (lowest level)
    for i in range(n): memo[1 << (1 + i)] = i

    def g(op, a, c_):
        gates.append((op, a, c_)); lvl.append(1 + max(lvl[a], lvl[c_])); return n + len(gates) - 1

    def offer(f, s):
        if f not in memo or lvl[memo[f]] > lvl[s]: memo[f] = s
    if parent is not None:
        pf = SK.parent_forms(dict(sk, n=n, m=len(sk['outputs'])), parent)
        for op, a, c_ in parent.gates:
            gates.append((op, a, c_)); lvl.append(1 + max(lvl[a], lvl[c_]))
        for j in range(len(parent.gates)):
            f = pf[n + j]
            if f is None: continue
            s_ = n + j
            if not (f & 1) and f and (f & (f - 1)) == 0 and (f.bit_length() - 1) > n:
                pos_sig.setdefault(f.bit_length() - 1, s_)
            offer(f, s_)

    def term_levels(f):
        return [lvl[pos_sig[p]] for p in range(1, f.bit_length()) if (f >> p) & 1]

    def feasible(f, L):
        if f & ~1 == 0: return L >= 0
        t = term_levels(f)
        return huff(t, f & 1) <= L

    def build(f, L):
        """signal for form f (const bit allowed) at level <= L"""
        if f in memo and lvl[memo[f]] <= L: return memo[f]
        base = f & ~1; c = f & 1
        if base == 0: raise ValueError('constant')
        nterms = bin(base).count('1')
        if nterms == 1 and not c:
            return pos_sig[base.bit_length() - 1]
        # greedy reuse
        best = None
        for fm, s in memo.items():
            if lvl[s] > L - 1: continue
            fb = fm & ~1
            if fb == 0 or fb & ~base: continue
            ov = bin(fb).count('1')
            if ov < 2 or fb == base: continue
            rest = f ^ fm
            if not feasible(rest, L - 1): continue
            if best is None or ov > best[0]: best = (ov, fm, s)
        if best is not None:
            ov, fm, s = best
            rest = f ^ fm
            if rest & ~1 == 0:                       # f = fm ^ 1
                s2 = g(NOT, s, s); offer(f, s2); return s2
            if (rest & ~1) and bin(rest & ~1).count('1') == 1 and (rest & 1):
                r = build(rest & ~1, L - 1); s2 = g(XNOR, s, r); offer(f, s2); return s2
            r = build(rest, L - 1)
            s2 = g(XOR, s, r); offer(f, s2); return s2
        # Huffman
        h = [(lvl[pos_sig[p]], 1 << p, pos_sig[p]) for p in range(1, base.bit_length()) if (base >> p) & 1]
        heapq.heapify(h)
        while len(h) > 1:
            l1, f1, s1 = heapq.heappop(h); l2, f2, s2 = heapq.heappop(h)
            ff = f1 ^ f2
            if not h and c:
                s = g(XNOR, s1, s2); offer(ff | 1, s); return s
            if ff in memo and lvl[memo[ff]] <= max(l1, l2) + 1: s = memo[ff]
            else: s = g(XOR, s1, s2); offer(ff, s)
            heapq.heappush(h, (lvl[s], ff, s))
        l, ff, s = h[0]
        if c:
            s2 = g(NOT, s, s); offer(ff | 1, s2); return s2
        return s

    for k, (L, R) in enumerate(sk['ands']):
        p = 1 + n + k
        if p in pos_sig: continue
        need = arr[p] - 1
        a = build(L, need); bb = build(R, need)
        s = g(AND, a, bb); pos_sig[p] = s; offer(1 << p, s)
    outs = [build(F, cap) for F in sk['outputs']]
    return core.Circuit(n, len(outs), gates, outs, 'reqsynth').live()


if __name__ == '__main__':
    d = json.load(open(sys.argv[1]))
    sk = {'ands': [(int(L, 16), int(R, 16)) for L, R in d['ands']], 'outputs': [int(F, 16) for F in d['outputs']]}
    parent = core.read_ncff(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3] != '-' else None
    cap = int(sys.argv[4]) if len(sys.argv) > 4 else 11
    c = synth(sk, parent=parent, cap=cap)
    assert tuple(c.value_table()) == tuple(targets.aes_sbox()), 'wrong function'
    model = core.Model.load('nist'); m = c.metrics(model)
    print(json.dumps({k: m[k] for k in ('A', 'AD', 'G', 'GD')}))
    Path(sys.argv[2]).write_text(core.write_ncff(c, model, comments=['T4 reqsynth of %s' % sys.argv[1]]))
