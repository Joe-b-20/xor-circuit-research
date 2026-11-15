#!/usr/bin/env python3
"""P7: optimise the GF(16) inversion of a GD10 tower circuit as a 4-input sub-problem.

The sub-circuit between the four N-coordinate signals (gate level 4) and the four base Y-forms
(gate level 7) is cut out as a 4-input, 4-output circuit (complement twins of the coordinates
become NOT gates), polished by the gate kernel under gate depth 3 / AND depth 3 (so the Y-forms stay
at level 7), and spliced back.

    invsub.py CIRCUIT --fsigs 78,79,80,83 [--seeds 1-20] [--iters 400000] [--out DIR]
"""
import argparse, importlib.util, os, sys, tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s1lib as L  # noqa: E402
import bopt  # noqa: E402
from bbuild import Net  # noqa: E402
from boolflux import targets  # noqa: E402
core = L.core
MODEL = core.Model.load(str(core.MODELS / 'nist.json'))
NOT = 3
os.environ.setdefault('F_BFX', str(Path.home() / 'xs-campaigns/2026-11-15-targets/P7/bin/bfx-94a75e2c18'))
spec = importlib.util.spec_from_file_location('fdrive', str(HERE.parent / 'F' / 'fdrive.py'))
FD = importlib.util.module_from_spec(spec); spec.loader.exec_module(FD)


def extract(c, fsigs, ysigs):
    n = c.n; T, lg, la = L.sim(c)
    leaf = {s: k for k, s in enumerate(fsigs)}
    comp = {}
    for s in range(n, n + len(c.gates)):
        for k, f in enumerate(fsigs):
            if s != f and T[s] == T[f] ^ L.ONES: comp[s] = k
    gates = []; idx = {}
    for k in range(4): pass

    def get(s):
        if s in leaf: return leaf[s]
        if s in idx: return idx[s]
        if s in comp:
            gates.append((NOT, comp[s], comp[s])); idx[s] = 4 + len(gates) - 1; return idx[s]
        if s < n: raise ValueError('cone reaches input x%d' % s)
        op, a, b = c.gates[s - n]
        if op in core.NONLINEAR_OPS and la[s] <= 1: raise ValueError('cone reaches AND-level-1 gate %d' % s)
        ia = get(a); ib = get(b)
        gates.append((op, ia, ib)); idx[s] = 4 + len(gates) - 1
        return idx[s]
    outs = [get(y) for y in ysigs]
    return core.Circuit(4, len(ysigs), gates, outs, 'inv').live()


def splice(c, fsigs, ysigs, sub):
    net = Net(c); n = c.n
    m = {k: fsigs[k] for k in range(4)}
    for j, (op, a, b) in enumerate(sub.gates):
        m[4 + j] = net.add(op, m[a], m[b])
    red = {y: m[o] for y, o in zip(ysigs, sub.outputs)}
    for s, (op, a, b) in list(net.nodes.items()):
        if s >= 100000: continue
        net.nodes[s] = (op, red.get(a, a), red.get(b, b))
    outs = [red.get(o, o) for o in c.outputs]
    return net.emit(outs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('circuit'); ap.add_argument('--fsigs', required=True)
    ap.add_argument('--seeds', default='1-10'); ap.add_argument('--iters', type=int, default=400000)
    ap.add_argument('--out', default=None); ap.add_argument('--seconds', type=float, default=60)
    a = ap.parse_args()
    c = L.load(a.circuit)
    T, lg, la, base = bopt.base_front(c)
    ysigs = [b[2] for b in base]
    fsigs = [int(x) for x in a.fsigs.split(',')]
    sub = extract(c, fsigs, ysigs)
    m0 = sub.metrics(MODEL)
    print('sub-circuit: G %d A %d GD %d AD %d' % (m0['G'], m0['A'], m0['GD'], m0['AD']), m0['counts'])
    full0 = splice(c, fsigs, ysigs, sub)
    assert full0.value_table() == targets.aes_sbox()
    print('re-spliced original: G', full0.metrics(MODEL)['G'])
    lo, hi = [int(x) for x in a.seeds.split('-')]
    wd = Path(tempfile.mkdtemp(prefix='p7inv'))
    best = (m0['G'], sub)
    for seed in range(lo, hi + 1):
        out, _ = FD.kernel(sub, wd, 's%d' % seed, 3, 3, a.iters, seed, extra={"gdw.3": 0, "repair_keep": 1}, seconds=a.seconds)
        mm = out.metrics(MODEL)
        full = splice(c, fsigs, ysigs, out)
        ok = full.value_table() == targets.aes_sbox()
        fm = full.metrics(MODEL)
        print('seed %d: sub G %d A %d GD %d AD %d -> full %d/%d/%d/%d ok=%s' % (
            seed, mm['G'], mm['A'], mm['GD'], mm['AD'], fm['A'], fm['AD'], fm['G'], fm['GD'], ok), flush=True)
        if ok and fm['GD'] <= 10 and fm['A'] <= 59 and fm['G'] < full0.metrics(MODEL)['G']:
            if a.out:
                Path(a.out).mkdir(parents=True, exist_ok=True)
                p = Path(a.out) / ('inv-s%d-a%d-g%d-gd%d.circ.txt' % (seed, fm['A'], fm['G'], fm['GD']))
                p.write_text(core.write_ncff(full, MODEL, comments=['P7 invsub.py seed %d from %s' % (seed, a.circuit)]))
                print('  saved', p)


if __name__ == '__main__':
    main()
