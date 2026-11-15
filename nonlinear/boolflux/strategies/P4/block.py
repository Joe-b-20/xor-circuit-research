"""P4: extract a block (window) of a circuit given input and output signal names, compute its
truth tables over the block inputs, and run exact synthesis on it.

    python3 block.py CIRC --ins t30,t31,t32,t33 --outs t36,... --steps 17 --amax 5 [--depth]
"""
import argparse
import json
import sys
import time

import circ
import exact


def block_tables(gates, ins, outs):
    n = len(ins)
    R = 1 << n
    vals = {name: sum(1 << t for t in range(R) if (t >> i) & 1) for i, name in enumerate(ins)}
    M = (1 << R) - 1
    used = []
    for op, o, gi in gates:
        if all(g in vals for g in gi) and o not in vals:
            a = [vals[g] for g in gi]
            vals[o] = (a[0] & a[1] if op == 'AND' else a[0] ^ a[1] if op == 'XOR' else
                       (a[0] ^ a[1]) ^ M if op == 'XNOR' else a[0] ^ M)
            used.append((op, o, gi))
    # gates in TFI of outs
    need = set(outs)
    blk = []
    for op, o, gi in reversed(used):
        if o in need:
            blk.append((op, o, gi))
            need |= set(gi)
    blk.reverse()
    return [vals[o] for o in outs], blk


def levels_of(gates):
    lvl = {f'x{i}': 0 for i in range(8)}
    for op, o, ins in gates:
        lvl[o] = 1 + max(lvl[i] for i in ins)
    return lvl


def required(gates, GD):
    """latest level each signal may have so that every output is <= GD"""
    req = {f'y{i}': GD for i in range(8)}
    for op, o, ins in reversed(gates):
        r = req.get(o, 10 ** 9)
        for i in ins:
            req[i] = min(req.get(i, 10 ** 9), r - 1)
    return req


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('circ')
    ap.add_argument('--ins', required=True)
    ap.add_argument('--outs', required=True)
    ap.add_argument('--steps', type=int, required=True)
    ap.add_argument('--amax', type=int, required=True)
    ap.add_argument('--amin', type=int, default=0)
    ap.add_argument('--depth', action='store_true', help='keep gate-level deadlines of the circuit (GD cap)')
    ap.add_argument('--gd', type=int, default=None)
    ap.add_argument('--budget', type=int, default=None)
    ap.add_argument('--nosym', action='store_true')
    a = ap.parse_args()
    gates = circ.read(a.circ)
    ins, outs = a.ins.split(','), a.outs.split(',')
    tts, blk = block_tables(gates, ins, outs)
    print('block gates', len(blk), 'ANDs', sum(g[0] == 'AND' for g in blk), file=sys.stderr)
    lv = None
    if a.depth:
        gd = a.gd or circ.metrics(gates)[3]
        L = levels_of(gates)
        # required times computed with the block's internal gates excluded from the backward pass
        names = {g[1] for g in blk}
        outside = [g for g in gates if g[1] not in names]
        req = required(outside, gd)
        base = min(L[i] for i in ins)
        arr = [L[i] - base for i in ins]
        dead = [req.get(o, 10 ** 9) - base for o in outs]
        Lmax = max(dead)
        lv = (arr, dead, Lmax)
        print('arrivals', arr, 'deadlines', dead, file=sys.stderr)
    st, res, el = exact.synth(len(ins), tts, a.steps, a.amax, a.amin, budget=a.budget, levels=lv, sym=not a.nosym)
    out = dict(status=st, elapsed=round(el, 2), steps=a.steps, amax=a.amax, ins=ins, outs=outs,
               depth=a.depth, block_gates=len(blk))
    if res:
        chain, om = res
        vals = exact.evaluate(len(ins), chain)
        assert all(vals[om[i]] == tts[i] for i in range(len(outs)))
        out['chain'] = chain
        out['outmap'] = om
    print(json.dumps(out))


if __name__ == '__main__':
    main()
