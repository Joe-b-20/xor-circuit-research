#!/usr/bin/env python3
"""P2 copy of T4 depthsynth (AND carry-over limited by arrivals). T4: depth-optimal synthesis of an AND skeleton: every form (AND operand, output) is built as a
Huffman XOR tree over its terms' arrival levels (combine the two earliest; a sub-sum already built
is reused).  The result meets the skeleton depth bound exactly (F's bound); gates are not minimised
(the kernel polishes afterwards under the depth cap).
    python3 depthsynth.py SKEL.json OUT.circ.txt
SKEL.json: {"ands": [[hexL, hexR], ...], "outputs": [hex, ...]} with n = 8 inputs.
"""
import sys, json, heapq
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core, targets  # noqa

AND, XOR, XNOR, NOT = 8, 6, 9, 3


def synth(sk, n=8, parent=None, arr=None):
    """P2 variant of T4 depthsynth: with arr (skeleton-bound arrivals per basis position), a parent AND
    is carried over only if its level is <= its skeleton arrival; slower ones are rebuilt."""
    gates = []; lvl = [0] * n
    pos_sig = {1 + i: i for i in range(n)}
    memo = {}                                   # form (no const) -> signal
    if parent is not None:
        # copy the whole parent; every parent signal whose form exists in this skeleton's basis
        # is offered for reuse (AND gates whose core table equals a skeleton AND become that AND)
        from boolflux import skeleton as SK
        pf = SK.parent_forms(dict(sk, n=n, m=len(sk['outputs'])), parent)
        for op, a, b in parent.gates:
            gates.append((op, a, b)); lvl.append(1 + max(lvl[a], lvl[b]))
        ok = [True] * n            # parent signal depends only on carried-over ANDs
        for j, (op, a, b) in enumerate(parent.gates):
            f = pf[n + j]; s_ = n + j
            if op in core.NONLINEAR_OPS:
                good = (f is not None and ok[a] and ok[b] and not (f & 1) and f & ~1 and (f & ~1) & ((f & ~1) - 1) == 0
                        and (f.bit_length() - 1) > n and (arr is None or lvl[s_] <= arr[f.bit_length() - 1]))
                if good: pos_sig.setdefault(f.bit_length() - 1, s_)
                ok.append(bool(good) and pos_sig.get(f.bit_length() - 1) == s_)
            else:
                ok.append(ok[a] and ok[b])
            if f is None or not ok[s_]: continue
            if f not in memo or lvl[memo[f]] > lvl[s_]: memo[f] = s_

    def g(op, a, b):
        gates.append((op, a, b)); lvl.append(1 + max(lvl[a], lvl[b])); return n + len(gates) - 1

    def build(f):
        c = f & 1; base = f & ~1
        if base == 0: raise ValueError('constant form')
        terms = [p for p in range(1, base.bit_length()) if (base >> p) & 1]
        h = [(lvl[pos_sig[p]], 1 << p, pos_sig[p]) for p in terms]
        hl = [x[0] for x in h]; heapq.heapify(hl)
        while len(hl) > 1:
            x1 = heapq.heappop(hl); x2 = heapq.heappop(hl); heapq.heappush(hl, max(x1, x2) + 1)
        target = hl[0] + (1 if (c and len(terms) == 1) else 0)
        if base in memo and not c and lvl[memo[base]] <= target: return memo[base]
        if c and f in memo and lvl[memo[f]] <= target: return memo[f]
        heapq.heapify(h)
        while len(h) > 1:
            l1, f1, s1 = heapq.heappop(h); l2, f2, s2 = heapq.heappop(h)
            ff = f1 ^ f2
            last = not h
            if last and c:
                s = g(XNOR, s1, s2)            # complement absorbed into the final XOR
                memo.setdefault(ff | 1, s)
                return s
            if ff in memo and lvl[memo[ff]] <= max(l1, l2) + 1: s = memo[ff]
            else: s = g(XOR, s1, s2); memo[ff] = s
            heapq.heappush(h, (lvl[s], ff, s))
        l, ff, s = h[0]
        if c:
            if (ff | 1) in memo and lvl[memo[ff | 1]] <= l + 1: return memo[ff | 1]
            s2 = g(NOT, s, s); memo[ff | 1] = s2; return s2
        return s

    for k, (L, R) in enumerate(sk['ands']):
        if (1 + n + k) in pos_sig: continue          # carried over from the parent
        a = build(L); b = build(R)
        s = g(AND, a, b); pos_sig[1 + n + k] = s; memo[1 << (1 + n + k)] = s
    outs = [build(F) for F in sk['outputs']]
    return core.Circuit(n, len(outs), gates, outs, 'depthsynth').live()


if __name__ == '__main__':
    d = json.load(open(sys.argv[1]))
    sk = {'ands': [(int(L, 16), int(R, 16)) for L, R in d['ands']], 'outputs': [int(F, 16) for F in d['outputs']]}
    parent = core.read_ncff(sys.argv[3]) if len(sys.argv) > 3 else None
    c = synth(sk, parent=parent)
    assert tuple(c.value_table()) == tuple(targets.aes_sbox()), 'wrong function'
    model = core.Model.load('nist')
    m = c.metrics(model)
    print(json.dumps({k: m[k] for k in ('A', 'AD', 'G', 'GD')}))
    Path(sys.argv[2]).write_text(core.write_ncff(c, model, comments=['T4 depthsynth of %s' % sys.argv[1]]))
