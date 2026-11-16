#!/usr/bin/env python3
"""Replace the GF(2^4) inversion block of a BP-style circuit by a synthesised one.

    python3 invsplice.py BASE.circ.txt INV.txt OUT.circ.txt

INV.txt: the gate list printed by invsyn.py ("OP name = a b" lines over x0..x3 and gXXXX names,
targets identified by their 16-bit tables).  The base circuit's inversion inputs and outputs
are found by invspec.spec; every consumer of an old inversion output is rewired to the new
gate with the same projected table; dead gates are removed.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3])); sys.path.insert(0, str(HERE))
from boolflux import core, targets   # noqa: E402
from invspec import spec, project   # noqa: E402

OPC = {'XOR': 6, 'XNOR': 9, 'AND': 8, 'NOT': 3}
X = [0xAAAA, 0xCCCC, 0xF0F0, 0xFF00]


def parse_inv(text):
    gates = []
    for ln in text.splitlines():
        m = re.match(r'\s*(XOR|XNOR|AND|NOT)\s+(\S+)\s*=\s*(\S+)\s*(\S*)', ln)
        if m: gates.append((m.group(1), m.group(2), m.group(3), m.group(4) or m.group(3)))
    return gates


def splice(base, inv_gates):
    n = base.n
    ins, outs, tabs, lv = spec(base)
    import itertools
    M0 = 0xFFFF
    pv = {'x%d' % k: X[k] for k in range(4)}
    for op, out, a, b in inv_gates:
        for nm in (a, b):
            if nm.startswith('e'): pv[nm] = int(nm[1:], 16)
        va, vb = pv[a], pv[b]
        pv[out] = {'XOR': va ^ vb, 'XNOR': va ^ vb ^ M0, 'AND': va & vb, 'NOT': va ^ M0}[op]
    produced = set(pv.values())
    chosen = None
    for sub in itertools.combinations(ins, 4):
        for perm in itertools.permutations(sub):
            proj = project(list(perm), outs, tabs)
            if proj is not None and all(t in produced for t in proj):
                chosen = list(perm); break
        if chosen: break
    if chosen is None: raise ValueError('no input order of the inversion inputs matches the block')
    ins = chosen
    proj = project(ins, outs, tabs)
    # new gates appended after the inversion inputs: simplest is to append at the end and
    # re-sort topologically by rebuilding from the outputs
    gates = list(base.gates)
    name = {'x%d' % k: ins[k] for k in range(4)}
    val = {'x%d' % k: X[k] for k in range(4)}
    M = 0xFFFF
    # extra level-0 inputs (names eXXXX = XOR of inversion inputs): XOR chains of the inputs
    for op, out, a, b in inv_gates:
        for nm in (a, b):
            if nm.startswith('e') and nm not in name:
                v = int(nm[1:], 16); ks = [k for k in range(4)]
                # solve v = xor of X[k] for a subset (X are independent)
                sub = [k for k in range(4) if any(((v >> i) & 1) != 0 for i in [1 << k]) ]
                sub = [k for k in range(4) if (v >> (1 << k)) & 1]
                assert v == eval('^'.join(str(X[k]) for k in sub)), nm
                # full 256-bit table of the extra; best pair (u, v) of existing signals with
                # tab[u] ^ tab[v] == it, minimising the larger level (cancellation in the mid layer)
                te = 0
                for k in sub: te ^= tabs[ins[k]]
                lvl = [0] * n
                for op_, a_, b_ in base.gates: lvl.append(1 + max(lvl[a_], lvl[b_]))
                where = {}
                for s_ in range(n + len(base.gates)):
                    t_ = tabs[s_]
                    if t_ not in where or lvl[s_] < lvl[where[t_]]: where[t_] = s_
                bestp = None
                for s_ in range(n + len(base.gates)):
                    o_ = where.get(te ^ tabs[s_])
                    if o_ is not None and o_ != s_:
                        key = max(lvl[s_], lvl[o_])
                        if bestp is None or key < bestp[0]: bestp = (key, s_, o_)
                # level limit for an extra input (default: the deepest inversion input; env BOOLFLUX_EXTRA_LEVEL)
                lim = int(__import__("os").environ.get("BOOLFLUX_EXTRA_LEVEL", str(max(lvl[q] for q in ins))))
                tri = None
                if bestp is not None and bestp[0] + 1 > lim:
                    # two-gate version: (u ^ v) ^ w with every operand at level <= lim - 2 / lim - 1
                    low2 = [s_ for s_ in range(n + len(base.gates)) if lvl[s_] <= lim - 2]
                    low1 = {}
                    for s_ in range(n + len(base.gates)):
                        if lvl[s_] <= lim - 1 and (tabs[s_] not in low1 or lvl[s_] < lvl[low1[tabs[s_]]]): low1[tabs[s_]] = s_
                    tri = None
                    for i_, u_ in enumerate(low2):
                        for v_ in low2[i_ + 1:]:
                            w_ = low1.get(te ^ tabs[u_] ^ tabs[v_])
                            if w_ is not None and w_ not in (u_, v_):
                                tri = (u_, v_, w_); break
                        if tri: break
                    if tri:
                        gates.append((6, tri[0], tri[1])); p_ = n + len(gates) - 1
                        gates.append((6, p_, tri[2])); cur = n + len(gates) - 1
                        bestp = None
                if tri:
                    pass
                elif bestp is not None:
                    gates.append((6, bestp[1], bestp[2])); cur = n + len(gates) - 1
                else:
                    cur = ins[sub[0]]
                    for k in sub[1:]:
                        gates.append((6, cur, ins[k])); cur = n + len(gates) - 1
                name[nm] = cur; val[nm] = v
    for op, out, a, b in inv_gates:
        va, vb = val[a], val[b]
        v = {'XOR': va ^ vb, 'XNOR': va ^ vb ^ M, 'AND': va & vb, 'NOT': va ^ M}[op]
        gates.append((OPC[op], name[a], name[b])); name[out] = n + len(gates) - 1; val[out] = v
    bytab = {}
    for k, v in val.items(): bytab.setdefault(v, name[k])
    remap = {}
    for s, t in zip(outs, proj):
        if t not in bytab: raise ValueError('inversion output %04x not produced' % t)
        remap[s] = bytab[t]
    # rewire consumers (only gates outside the inversion block, i.e. original gates)
    new = []
    for j, (op, a, b) in enumerate(gates):
        if j < len(base.gates):
            a = remap.get(a, a); b = remap.get(b, b)
        new.append((op, a, b))
    outsig = [remap.get(o, o) for o in base.outputs]
    # topological rebuild
    S = n + len(new)
    order = []; state = {}
    def visit(s):
        st = [s]
        while st:
            x = st[-1]
            if x < n or state.get(x) == 2: st.pop(); continue
            op, a, b = new[x - n]
            pend = [y for y in (a, b) if y >= n and state.get(y) != 2]
            if pend and state.get(x) != 1:
                state[x] = 1; st += pend; continue
            state[x] = 2; order.append(x); st.pop()
    for o in outsig: visit(o)
    pos = {i: i for i in range(n)}; g2 = []
    for x in order:
        op, a, b = new[x - n]
        pos[x] = n + len(g2); g2.append((op, pos[a], pos[b]))
    c = core.Circuit(n, base.m, g2, [pos[o] for o in outsig], 'invsplice', base.in_names, base.out_names).live()
    return c


if __name__ == '__main__':
    base = core.read_ncff(sys.argv[1])
    inv = parse_inv(Path(sys.argv[2]).read_text())
    c = splice(base, inv)
    m = c.metrics(); ok = c.value_table() == targets.aes_sbox()
    print('G=%d A=%d GD=%d AD=%d ok=%s' % (m['G'], m['A'], m['GD'], m['AD'], ok))
    if ok:
        Path(sys.argv[3]).write_text(core.write_ncff(c, core.Model.load(str(core.MODELS / 'nist.json'))), encoding='utf-8')
