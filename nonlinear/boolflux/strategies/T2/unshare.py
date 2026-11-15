#!/usr/bin/env python3
"""Depth-first restart point: keep the AND structure of a circuit, rebuild every linear signal that is read
by an AND or is an output as a depth-optimal XOR tree (Huffman on arrival times) over its atoms (inputs and
AND outputs), with hash-consing of equal sub-forms; constants on the root (XNOR) or a NOT.  The result has
the minimum gate depth reachable without changing the AND gates and their operand/output forms, and many
more gates; the gate kernel is then run from it under the target caps (walk.py), approaching the
G/GD trade-off from the shallow side instead of the cheap side.

  unshare.py IN(.bfx|.circ.txt|archive id) OUT.bfx [--archive DIR] [--seed S]
"""
import heapq
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from boolflux.hub.common import core, metrics, targets  # noqa: E402

XOR, XNOR, NOT, AND = 6, 9, 3, 8


def unshare(c, rng):
    n = c.n
    form = {}; cst = {}
    gates = []; arr = {}
    atom = {}          # old atom signal -> new signal
    for i in range(n): form[i] = 1 << i; cst[i] = 0; atom[i] = i; arr[i] = 0
    node = {}          # form (int over old atom ids) -> new signal (no constant)
    for i in range(n): node[1 << i] = i

    def build(f, k):
        if f == 0:
            raise ValueError('constant operand')
        if f in node and not k: return node[f]
        if f in node:
            s = node[f]; gates.append((NOT, s, s)); r = n + len(gates) - 1; arr[r] = arr[s] + 1; return r
        bits = [b for b in range(f.bit_length()) if (f >> b) & 1]
        h = [(arr[atom[b]], rng.random(), 1 << b) for b in bits]
        heapq.heapify(h)
        while len(h) > 1:
            a1, _, f1 = heapq.heappop(h); a2, _, f2 = heapq.heappop(h)
            fw = f1 ^ f2
            last = len(h) == 0
            if fw in node and not (last and k):
                s = node[fw]
            else:
                op = XNOR if (last and k) else XOR
                gates.append((op, node[f1], node[f2])); s = n + len(gates) - 1
                arr[s] = max(arr[node[f1]], arr[node[f2]]) + 1
                if op == XOR: node[fw] = s
                else: return s
            heapq.heappush(h, (arr[s], rng.random(), fw))
        return node[h[0][2]]

    for j, (op, a, b) in enumerate(c.gates):
        s = n + j
        if op == AND:
            x = build(form[a], cst[a]); y = build(form[b], cst[b])
            gates.append((AND, x, y)); r = n + len(gates) - 1; arr[r] = max(arr[x], arr[y]) + 1
            atom[s] = r; node[1 << s] = r; form[s] = 1 << s; cst[s] = 0
        elif op in (XOR, XNOR):
            form[s] = form[a] ^ form[b]; cst[s] = cst[a] ^ cst[b] ^ (1 if op == XNOR else 0)
        elif op == NOT:
            form[s] = form[a]; cst[s] = cst[a] ^ 1
        else:
            raise ValueError('op %d' % op)
    outs = [build(form[o], cst[o]) for o in c.outputs]
    return core.Circuit(n, c.m, gates, outs).live()


def unshare_partial(c, rng, p=0.5):
    """Copy the circuit; for each AND level k chosen with probability p (and the outputs, also with p)
    rebuild the operands of the ANDs of that level (the outputs) as depth-optimal XOR trees over atoms,
    hash-consed with every original linear signal (so equal partial sums reuse existing gates)."""
    from boolflux.hub.join import levels
    n = c.n; lv = levels(c)
    K = max(lv[n:] or [0])
    chosen = {k for k in range(1, K + 1) if rng.random() < p}
    outs_new = rng.random() < p
    if not chosen and not outs_new: chosen = {rng.randint(1, K)}
    gates = []; arr = {}; mp = {}; form = {}; cst = {}; node = {}
    for i in range(n): mp[i] = i; arr[i] = 0; form[i] = 1 << i; cst[i] = 0; node[1 << i] = i
    atom = {i: i for i in range(n)}

    def emit(op, a, b):
        gates.append((op, a, b)); s = n + len(gates) - 1
        arr[s] = max(arr[a], arr[b]) + 1; return s

    def build(f, k):
        if f in node and not k: return node[f]
        if f in node: s = node[f]; return emit(NOT, s, s)
        bits = [b for b in range(f.bit_length()) if (f >> b) & 1]
        h = [(arr[atom[b]], rng.random(), 1 << b) for b in bits]
        heapq.heapify(h)
        while len(h) > 1:
            a1, _, f1 = heapq.heappop(h); a2, _, f2 = heapq.heappop(h)
            fw = f1 ^ f2; last = len(h) == 0
            if fw in node and not (last and k): s = node[fw]
            else:
                op = XNOR if (last and k) else XOR
                s = emit(op, node[f1], node[f2])
                if op == XOR: node[fw] = s
                else: return s
            heapq.heappush(h, (arr[s], rng.random(), fw))
        return node[h[0][2]]

    for j, (op, a, b) in enumerate(c.gates):
        s = n + j
        if op == AND:
            if lv[s] in chosen: x = build(form[a], cst[a]); y = build(form[b], cst[b])
            else: x, y = mp[a], mp[b]
            r = emit(AND, x, y); mp[s] = r; atom[s] = r; form[s] = 1 << s; cst[s] = 0; node[1 << s] = r
        else:
            r = emit(op, mp[a], mp[b] if op != NOT else mp[a]); mp[s] = r
            if op == NOT: form[s] = form[a]; cst[s] = cst[a] ^ 1
            else: form[s] = form[a] ^ form[b]; cst[s] = cst[a] ^ cst[b] ^ (1 if op == XNOR else 0)
            if not cst[s] and form[s] not in node: node[form[s]] = r
    outs = [build(form[o], cst[o]) if outs_new else mp[o] for o in c.outputs]
    return core.Circuit(n, c.m, gates, outs).live()


def main():
    a = sys.argv[1:]; ar = None; seed = 1
    if '--archive' in a: i = a.index('--archive'); ar = Path(a[i + 1]); del a[i:i + 2]
    if '--seed' in a: i = a.index('--seed'); seed = int(a[i + 1]); del a[i:i + 2]
    src, dst = a
    p = Path(src)
    if p.exists(): c = core.from_kernel(p.read_text()) if p.suffix == '.bfx' else core.read_ncff(str(p))
    else: c = core.from_kernel((ar / 'archive' / (src + '.bfx')).read_text())
    nc = unshare(c, random.Random(seed))
    assert nc.value_table() == targets.aes_sbox()
    Path(dst).write_text(core.to_kernel(nc))
    print(metrics(c), '->', metrics(nc))


if __name__ == '__main__':
    main()
