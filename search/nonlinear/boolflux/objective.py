"""Objectives and ranking shared by the kernel config, cli.py, workflow.py and the benchmark tools.

An objective is a lexicographic key list such as 'cost,gd' or 'a,cost' (keys: cost, g, a, gd, ad).
Circuits are ranked feasibility first:

    rank(m) = (0 if every cap holds else 1, total cap excess, key_1, key_2, ...)

which is what the kernel does with `lex`.  For a circuit outside a depth cap the kernel also
ranks by VSUM, the summed path excess (over all gates, by how much the longest path through the
gate exceeds the cap), between the total excess and the keys; measure() computes it the same way,
so a repair that shortens too-deep paths without lowering the maximum yet counts as progress.  The weighted sum
(weights 1, 1e-4, 1e-8, ...) is kept only for the size of a Metropolis step inside the kernel.
"""
KEYS = {'cost': 'cost', 'g': 'G', 'a': 'A', 'gd': 'GD', 'ad': 'AD'}
WKEY = {'cost': 'w.cost', 'g': 'w.g', 'a': 'w.a', 'gd': 'w.gd', 'ad': 'w.ad'}


def parse(spec):
    keys = [k.strip().lower() for k in spec.split(',') if k.strip()]
    if not keys:
        raise SystemExit('empty objective')
    for k in keys:
        if k not in KEYS:
            raise SystemExit('unknown objective key %r (use %s)' % (k, ', '.join(KEYS)))
    if len(set(keys)) != len(keys):
        raise SystemExit('objective key repeated: %s' % spec)
    return keys


def weights(spec):
    """Kernel weights (Metropolis step size only) plus the exact lexicographic order `lex`."""
    keys = parse(spec)
    w = {v: 0.0 for v in WKEY.values()}
    for i, k in enumerate(keys):
        w[WKEY[k]] += 10.0 ** (-4 * i)
    w['lex'] = ','.join(keys)
    return w


def excess(mt, caps):
    return sum(max(0, mt[k] - c) for k, c in (caps or {}).items() if c is not None)


def feasible(mt, caps):
    return excess(mt, caps) == 0


def rank(mt, caps, spec):
    """Sort key: smaller is better.  Costs are rounded to 9 decimals so that sums of the same
    gate costs compare equal.  mt['VSUM'] (from measure) is used when present."""
    e = excess(mt, caps)
    return (0 if e == 0 else 1, e, mt.get('VSUM', 0) if e else 0) + tuple(round(float(mt[KEYS[k]]), 9) for k in parse(spec))


def path_excess(c, caps):
    """The kernel's VSUM (bfx.c metrics): sum over gates of the excess of the longest
    input-to-output path through the gate over the GD cap, plus the same for AND depth."""
    gd, ad = (caps or {}).get('GD'), (caps or {}).get('AD')
    if gd is None and ad is None:
        return 0
    from boolflux import core
    n, gates = c.n, c.gates
    tot = n + len(gates)
    LG = [0] * tot; LA = [0] * tot
    nl = [0] * tot
    for j, (op, a, b) in enumerate(gates):
        v = n + j; nl[v] = 1 if op in core.NONLINEAR_OPS else 0
        LG[v] = max(LG[a], LG[b]) + 1; LA[v] = max(LA[a], LA[b]) + nl[v]
    NEG = -10 ** 9
    HG = [NEG] * tot; HA = [NEG] * tot
    for o in c.outputs:
        HG[o] = 0; HA[o] = 0
    for j in range(len(gates) - 1, -1, -1):
        op, a, b = gates[j]; v = n + j
        hg, ha = HG[v] + 1, HA[v] + nl[v]
        for x in (a, b):
            if hg > HG[x]: HG[x] = hg
            if ha > HA[x]: HA[x] = ha
    s = 0
    for j in range(len(gates)):
        v = n + j
        if gd is not None and LG[v] + HG[v] > gd: s += LG[v] + HG[v] - gd
        if ad is not None and LA[v] + HA[v] > ad: s += LA[v] + HA[v] - ad
    return s


def measure(c, model, caps):
    """c.metrics(model) plus VSUM when the circuit violates a cap."""
    mt = c.metrics(model)
    if excess(mt, caps):
        mt['VSUM'] = path_excess(c, caps)
    return mt


def weighted(mt, spec):
    w = weights(spec)
    return sum(w[WKEY[k]] * mt[KEYS[k]] for k in KEYS)
