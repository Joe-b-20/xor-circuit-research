"""P4: rebuild an AES S-box circuit of the 103 family from parts:
  top   = a value set (forms + helpers) realised with earliest-level recipes,
  pre   = a product-part chain over a1..a9 plus x-linear injections at chosen points,
  rest  = the reference's gates from the inversion on (unchanged, same names).

Library:
  top_gates(values, names)        -> gates for the top layer, name of every value
  pre_extract(gates, s, targets)  -> (achain, P, X) of the reference's pre-inversion
  pre_gates(achain, targets, inj, vecname, prodnames) -> gates of a pre-inversion with injections
  assemble(...)                   -> full gate list, verified
"""
import circ
import topenum


def nm(v):
    return '+'.join(f'x{i}' for i in range(8) if v >> i & 1)


def top_gates(S, names):
    """S: set of vectors (non-input); names: dict vector->preferred name (others get h<k>)."""
    lvl = topenum.closure_levels(S)
    assert all(t in lvl for t in S), 'top value set not closed'
    vn = {1 << i: f'x{i}' for i in range(8)}
    k = 0
    for v in sorted(S, key=lambda v: lvl[v]):
        if v in names:
            vn[v] = names[v]
        else:
            k += 1
            vn[v] = f'h{k}'
    gates = []
    done = {1 << i for i in range(8)}
    for v in sorted(S, key=lambda v: (lvl[v], v)):
        best = None
        for a in done:
            b = a ^ v
            if b in done and a < b:
                l = max(lvl[a], lvl[b])
                if l + 1 == lvl[v]:
                    best = (a, b)
                    break
        assert best, nm(v)
        gates.append(('XOR', vn[v], (vn[best[0]], vn[best[1]])))
        done.add(v)
    return gates, vn, lvl


def pre_extract(gates, s, targets, prod):
    """Product-part chain of the reference's pre-inversion (gates whose atoms lie in x + prod)."""
    pidx = {p: i for i, p in enumerate(prod)}
    am = lambda atoms: sum(1 << pidx[t] for t in atoms if t in pidx)
    xm = lambda atoms: sum(1 << int(t[1:]) for t in atoms if t[0] == 'x')
    allowed = set(prod) | {f'x{i}' for i in range(8)}
    nodeval = [1 << i for i in range(len(prod))]
    sig2node = {p: i for i, p in enumerate(prod)}
    achain = []
    for op, o, ins in gates:
        if op == 'AND' or not (s[o][0] <= allowed) or am(s[o][0]) == 0:
            continue
        a, b = ins
        na, nb_ = sig2node.get(a), sig2node.get(b)
        if na is not None and nb_ is not None:
            achain.append((min(na, nb_), max(na, nb_)))
            nodeval.append(nodeval[na] ^ nodeval[nb_])
            sig2node[o] = len(nodeval) - 1
        else:
            sig2node[o] = na if na is not None else nb_
    P = [am(s[t][0]) for t in targets]
    X = [xm(s[t][0]) for t in targets]
    return achain, P, X


def pre_gates(achain, nb, P, targets, inj, xname, prodnames, consts, prefix='q'):
    """inj: list of (point, s) with point ('node', u) | ('edge', u, w) | ('out', j).
    xname: vector->signal name for injected values.  consts: wanted constant of each target.
    Returns gates; the targets get the names in `targets`."""
    import reinject
    vals, tnode, readers, pts = reinject.points(achain, nb, P)
    N = len(vals)
    name = {u: prodnames[u] for u in range(nb)}
    gates = []
    node_inj = {}
    edge_inj = {}
    out_inj = {}
    for p, sv in inj:
        if p[0] == 'node':
            node_inj.setdefault(p[1], []).append(sv)
        elif p[0] == 'edge':
            edge_inj.setdefault((p[1], p[2]), []).append(sv)
        else:
            out_inj.setdefault(p[1], []).append(sv)
    cnt = [0]

    def fresh():
        cnt[0] += 1
        return f'{prefix}{cnt[0]}'

    outname = {}

    def inject(sig, svs):
        for sv in svs:
            o = fresh()
            gates.append(['XOR', o, (sig, xname[sv])])
            sig = o
        return sig

    # leaf node injections
    cur = {}
    for u in range(nb):
        cur[u] = inject(name[u], node_inj.get(u, []))
    for i, (j, k) in enumerate(achain):
        u = nb + i
        a = inject(cur[j], edge_inj.get((j, u), []))
        b = inject(cur[k], edge_inj.get((k, u), []))
        o = fresh()
        gates.append(['XOR', o, (a, b)])
        cur[u] = inject(o, node_inj.get(u, []))
    for jj, t in enumerate(targets):
        sig = inject(cur[tnode[jj]], out_inj.get(jj, []))
        outname[jj] = sig
    # rename target signals to the reference names; a node feeding two targets needs care
    ren = {}
    for jj, t in enumerate(targets):
        ren[outname[jj]] = ren.get(outname[jj], []) + [t]
    final = []
    alias = {}
    for g in gates:
        op, o, ins = g
        ins = tuple(alias.get(i, i) for i in ins)
        if o in ren:
            first = ren[o][0]
            alias[o] = first
            final.append([op, first, ins])
            for extra in ren[o][1:]:
                raise RuntimeError('two targets share one node')
        else:
            final.append([op, o, ins])
    return final


def fix_consts(gates, want):
    """Flip XOR/XNOR of the gate producing each named signal so its constant matches want[name]."""
    s = circ.symbolic([tuple(g) for g in gates])
    out = []
    for op, o, ins in gates:
        out.append([op, o, ins])
    return out


def assemble(ref_gates, new_top, new_pre, drop_names):
    """Reference gates minus drop_names, plus new top/pre gates, topologically ordered."""
    keep = [g for g in ref_gates if g[1] not in drop_names]
    allg = [tuple(g) for g in new_top] + [tuple(g) for g in new_pre] + [tuple(g) for g in keep]
    have = {f'x{i}' for i in range(8)}
    out = []
    pending = list(allg)
    while pending:
        prog = False
        rest = []
        for g in pending:
            if all(i in have for i in g[2]):
                out.append(g)
                have.add(g[1])
                prog = True
            else:
                rest.append(g)
        pending = rest
        if not prog:
            raise RuntimeError('cannot order: ' + str(pending[:3]))
    # dead gate removal
    live = {f'y{i}' for i in range(8)}
    res = []
    for g in reversed(out):
        if g[1] in live:
            res.append(g)
            live |= set(g[2])
    res.reverse()
    return res


def set_constants(gates, ref_sym, names):
    """For each signal name in names whose constant differs from the reference, flip the producing
    XOR<->XNOR (only XOR-type producers)."""
    g2 = [list(g) for g in gates]
    for _ in range(3):
        s = circ.symbolic([tuple(g) for g in g2])
        changed = False
        for g in g2:
            if g[1] in names and g[1] in s and s[g[1]][1] != ref_sym[g[1]][1]:
                if g[0] in ('XOR', 'XNOR'):
                    g[0] = 'XNOR' if g[0] == 'XOR' else 'XOR'
                    changed = True
        if not changed:
            break
    return [tuple(g) for g in g2]
