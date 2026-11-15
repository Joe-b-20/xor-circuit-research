"""P4: exact resynthesis of a linear window W (a set of XOR/XNOR gates) by SAT over symbolic vectors.

    python3 linwin.py CIRC --gates t13,t20,...  --steps K [--gd 32] [--budget N] [--write OUT.circ.txt]

Targets  = values of W's gates read outside W (by ANDs, by later XORs, or primary outputs).
Base     = every signal outside W and outside TFO(W) (free; inputs, earlier XORs, earlier ANDs).
Values are symbolic vectors over atoms (inputs + AND outputs); constants are free (XNOR = XOR cost).
Arrivals are the base signals' gate levels; deadlines are the required times of the targets with W
removed (backward pass from GD on the rest of the circuit).  A SAT answer is spliced back and the
whole circuit is re-verified on all 256 inputs.
[C] for UNSAT: no circuit of K XOR gates over those base signals computes the targets within the
deadlines (same AND gates, same everything outside W).
"""
import argparse
import json
import sys
import time

import block
import circ
import linslp2 as linslp


def run(gates, W, steps, gd, budget=None, depth=True, sym=True):
    s = circ.symbolic(gates)
    Wset = set(W)
    readers = {}
    for op, o, ins in gates:
        for i in ins:
            readers.setdefault(i, set()).add(o)
    # TFO of W
    tfo = set()
    for op, o, ins in gates:
        if o in Wset or any(i in Wset or i in tfo for i in ins):
            if o not in Wset:
                tfo.add(o)
    outs = {f'y{i}' for i in range(8)}
    targets = [o for o in W if (readers.get(o, set()) - Wset) or o in outs]
    xs = [f'x{i}' for i in range(8)]
    base_names = xs + [o for op, o, ins in gates if o not in Wset and o not in tfo]
    tatoms = set().union(*[s[t][0] for t in targets])
    base_names = [n for n in base_names if s[n][0] <= tatoms]
    atoms = sorted({a for n in base_names + targets for a in s[n][0]},
                   key=lambda t: (t[0], int(t[1:])))
    idx = {a: i for i, a in enumerate(atoms)}
    vec = lambda n: sum(1 << idx[a] for a in s[n][0])
    base = []
    bnames = []
    for n in base_names:
        v = vec(n)
        if v and v not in base:
            base.append(v)
            bnames.append(n)
    tv = [vec(t) for t in targets]
    L = block.levels_of(gates)
    rest = [g for g in gates if g[1] not in Wset]
    req = block.required(rest, gd)
    arr = [L[n] for n in bnames]
    dl = [req.get(t, 10 ** 6) for t in targets]
    # a target that equals a base vector needs no gate, but its deadline must hold
    keep = [i for i, v in enumerate(tv) if v not in base]
    Lmax = max(dl[i] for i in keep)
    # base signals arriving at or after Lmax can never be read by a target cone; drop them
    sel = [i for i, a in enumerate(arr) if a < Lmax] if depth else list(range(len(base)))
    base2 = [base[i] for i in sel]
    bn2 = [bnames[i] for i in sel]
    arr2 = [arr[i] for i in sel]
    tg2 = [tv[i] for i in keep]
    dl2 = [dl[i] for i in keep]
    st, ch, el = linslp.slp(len(atoms), base2, tg2, steps, budget=budget,
                            arrivals=arr2 if depth else None, deadlines=dl2 if depth else None, sym=sym)
    info = dict(status=st, steps=steps, window=len(W), targets=targets, base=len(base2), dims=len(atoms),
                elapsed=round(el, 2), deadlines=dl2)
    if st != 'sat':
        return info, None
    # splice
    vals = linslp.values(base2, ch)
    names = list(bn2)
    newg = []
    sym_of = {}
    for n in bn2:
        sym_of[n] = s[n]
    for k, (j, kk) in enumerate(ch):
        nm = f'p4w{k}'
        a, b = names[j], names[kk]
        c = sym_of[a][1] ^ sym_of[b][1]
        newg.append(['XOR', nm, (a, b)])
        sym_of[nm] = (sym_of[a][0] ^ sym_of[b][0], c)
        names.append(nm)
    # map targets: find node with same vector; fix constant with XNOR on the producing gate if needed
    rename = {}
    for t in targets:
        v = vec(t)
        if v in base2 and v not in vals[len(base2):]:
            src = bn2[base2.index(v)]
            if s[src][1] != s[t][1]:
                # needs a complement: one NOT gate (costs 1); record
                newg.append(['NOT', f'p4n_{t}', (src,)])
                src = f'p4n_{t}'
            rename[t] = src
            continue
        i = vals.index(v, len(base2))
        g = newg[i - len(base2)]
        want = s[t][1]
        have = sym_of[g[1]][1]
        if have != want:
            if g[0] == 'XOR':
                g[0] = 'XNOR'
                sym_of[g[1]] = (sym_of[g[1]][0], want)
            else:
                g[0] = 'XOR'
                sym_of[g[1]] = (sym_of[g[1]][0], want)
            # any other target using this node with the other constant would need a NOT
        rename[t] = g[1]
    # complement conflicts: two targets mapped to the same node with different constants
    out = []
    pos = None
    for gi, (op, o, ins) in enumerate(gates):
        if o in Wset:
            continue
        out.append((op, o, ins))
    # insert new gates after the last base gate they need: simplest: topological merge
    have = set(xs)
    pending = [tuple(g) for g in newg]
    result = []
    rest_gates = [(op, o, tuple(rename.get(i, i) for i in ins)) for op, o, ins in out]
    queue = rest_gates
    while queue or pending:
        progressed = False
        for g in list(pending):
            if all(i in have for i in g[2]):
                result.append(g)
                have.add(g[1])
                pending.remove(g)
                progressed = True
        if queue and all(i in have for i in queue[0][2]):
            g = queue.pop(0)
            result.append(g)
            have.add(g[1])
            progressed = True
        if not progressed:
            raise RuntimeError('splice: cannot order')
    # outputs renamed?  if a target was a primary output, add a BUF-free rename by renaming the gate
    for t in targets:
        if t in outs and rename.get(t) != t:
            r = rename[t]
            result = [(op, (t if o == r else o), tuple(t if i == r else i for i in ins)) for op, o, ins in result]
    # remove dead gates
    live = set(outs)
    keepg = []
    for g in reversed(result):
        if g[1] in live:
            keepg.append(g)
            live |= set(g[2])
    keepg.reverse()
    return info, keepg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('circ')
    ap.add_argument('--gates', required=True)
    ap.add_argument('--steps', type=int, required=True)
    ap.add_argument('--gd', type=int, default=None)
    ap.add_argument('--budget', type=int, default=None)
    ap.add_argument('--nodepth', action='store_true')
    ap.add_argument('--write', default=None)
    a = ap.parse_args()
    gates = circ.read(a.circ)
    gd = a.gd or circ.metrics(gates)[3]
    W = a.gates.split(',')
    info, newc = run(gates, W, a.steps, gd, a.budget, depth=not a.nodepth)
    if newc is not None:
        ok = circ.correct(newc)
        info['correct'] = ok
        info['metrics'] = circ.metrics(newc)
        if a.write and ok:
            circ.write(a.write, newc, 'p4-linwin', comment=[f'P4 linwin from {a.circ} W={a.gates} steps={a.steps}'])
    print(json.dumps(info))


if __name__ == '__main__':
    main()
