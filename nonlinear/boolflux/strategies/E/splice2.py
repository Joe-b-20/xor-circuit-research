#!/usr/bin/env python3
"""Stage transplant with linear interface (Track E, M3b).

For circuits X (front donor) and Y (back donor) and cut level LY: the cut of Y is the set of Y
signals of AND level <= LY that are read by a gate of level > LY or are outputs.  Every cut signal
must lie in the affine span of X's front (inputs and X's ANDs of level <= LX); it is then rebuilt
greedily from X's front signals (XOR of existing linear forms, largest overlap first; XNOR/NOT for
the constant).  The result = X's front + interface XORs + Y's gates above the cut, dead gates
removed, checked on all 256 inputs.

    python3 splice2.py OUTDIR FILE...     (all ordered pairs; LY over all cut levels; LX in {LY, AD_X-1})
Writes OUTDIR/splices.json (summary rows, bounded) and OUTDIR/cands/*.bfx for rows with need <= NEED_MAX.
"""
import json, sys, time, hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import core, load, metrics, correct, levels, ONES   # noqa: E402

XOR, XNOR, NOT = 6, 9, 3
NEED_MAX = 10
MAX_ROWS = 200000


class Front:
    """X's front up to level LX: basis elimination (tables -> forms over basis ids) and the forms of
    every front signal."""
    def __init__(self, X, tx, lx, LX):
        n = X.n
        self.X = X; self.n = n
        basis = [ONES] + [tx[i] for i in range(n)]     # id 0 = const, 1..n inputs, then ANDs
        self.sig_of_basis = [None] + list(range(n))
        for j, (op, a, b) in enumerate(X.gates):
            s = n + j
            if op in core.NONLINEAR_OPS and lx[s] <= LX:
                basis.append(tx[s]); self.sig_of_basis.append(s)
        self.piv = []      # (pivot bit, table, form)
        for i, t in enumerate(basis):
            f = 1 << i
            for p, rt, rf in self.piv:
                if (t >> p) & 1: t ^= rt; f ^= rf
            if t:
                self.piv.append((t.bit_length() - 1, t, f))
                self.piv.sort(key=lambda r: -r[0])
        # forms of front signals
        self.have = {}
        for s in range(n + len(X.gates)):
            if lx[s] <= LX:
                f = self.form(tx[s])
                if f is not None and f not in self.have: self.have[f] = s

    def form(self, t):
        f = 0
        for p, rt, rf in self.piv:
            if (t >> p) & 1: t ^= rt; f ^= rf
        return f if t == 0 else None


def build(front, f, gates, have):
    """signal for form f (constant bit 0 handled by caller)."""
    if f in have: return have[f]
    parts = []; rest = f
    while rest:
        best = None; bg = 0
        for fm, s in have.items():
            if fm & 1: continue
            g = bin(rest).count('1') - bin(rest ^ fm).count('1')
            if g > bg: best, bg = (fm, s), g
        if best is None:
            return None
        parts.append(best); rest ^= best[0]
    af, asg = parts[0]
    for fm, s in parts[1:]:
        af ^= fm
        if af in have: asg = have[af]
        else:
            gates.append((XOR, asg, s)); asg = front.n + len(gates) - 1; have[af] = asg
    return asg


def splice(front, Y, ty, ly, LY):
    n = Y.n
    X = front.X
    gates = list(X.gates)
    have = dict(front.have)
    # cut of Y
    need = [False] * (n + len(Y.gates))
    for j, (op, a, b) in enumerate(Y.gates):
        if ly[n + j] > LY:
            for o in (a, b):
                if o >= n and ly[o] <= LY: need[o] = True
    for o in Y.outputs:
        if o >= n and ly[o] <= LY: need[o] = True
    ymap = list(range(n)) + [None] * len(Y.gates)
    nint = 0
    for s in range(n, n + len(Y.gates)):
        if not need[s]: continue
        f = front.form(ty[s])
        if f is None: return None, None
        if f in have: ymap[s] = have[f]; continue
        base = f & ~1
        if base == 0: return None, None
        g0 = len(gates)
        sg = build(front, base, gates, have)
        if sg is None: return None, None
        if f & 1:
            if (f in have): sg = have[f]
            elif sg >= n and gates[sg - n][0] == XOR and sg - n >= g0:
                op, a, b = gates[sg - n]; gates[sg - n] = (XNOR, a, b); have.pop(base, None); have[f] = sg
            else:
                gates.append((NOT, sg, sg)); sg = n + len(gates) - 1; have[f] = sg
        nint += len(gates) - g0
        ymap[s] = sg
    for j, (op, a, b) in enumerate(Y.gates):
        s = n + j
        if ly[s] <= LY: continue
        if ymap[a] is None or ymap[b] is None: return None, None
        gates.append((op, ymap[a], ymap[b])); ymap[s] = n + len(gates) - 1
    outs = [ymap[o] for o in Y.outputs]
    if any(o is None for o in outs): return None, None
    return core.Circuit(n, Y.m, gates, outs).live(), nint


def main():
    out = Path(sys.argv[1]); (out / 'cands').mkdir(parents=True, exist_ok=True)
    args = sys.argv[2:]; shard = (0, 1)
    if args and args[0] == '--shard':
        a, b = args[1].split('/'); shard = (int(a), int(b)); args = args[2:]
    if len(args) == 1 and args[0].endswith('.list'): args = Path(args[0]).read_text().split()
    files = [Path(a) for a in args]
    circs = []; names = set()
    for f in files:
        c = load(f)
        if not correct(c): continue
        k = core.to_kernel(c)
        if k in names: continue
        names.add(k)
        circs.append((f.name, c, c.tables(), levels(c), metrics(c)))
    print('circuits', len(circs), flush=True)
    sys.path.insert(0, str(HERE.parents[1] / 'campaigns'))
    import aes_check
    pub = [u for (u, nm) in aes_check.published()]
    fronts = {}
    rows = []; seen = set(); t0 = time.time(); tried = 0
    for xi, (xn, X, tx, lx, mx) in enumerate(circs):
        for LX in range(1, mx[1]):
            fronts[(xi, LX)] = None
    for xi, (xn, X, tx, lx, mx) in enumerate(circs):
        if xi % shard[1] != shard[0]: continue
        fr = {LX: Front(X, tx, lx, LX) for LX in range(1, mx[1])}
        for yi, (yn, Y, ty, ly, my) in enumerate(circs):
            if xi == yi: continue
            for LY in range(1, my[1]):
                for LX in sorted({min(LY, mx[1] - 1), mx[1] - 1}):
                    tried += 1
                    c, nint = splice(fr[LX], Y, ty, ly, LY)
                    if c is None: continue
                    m = metrics(c)
                    h = hashlib.sha1(core.to_kernel(c).encode()).hexdigest()[:16]
                    if h in seen: continue
                    seen.add(h)
                    gs = [u[2] for u in pub if u[0] <= m[0] and u[1] <= m[1] and u[3] <= m[3]]
                    need = max(0, m[2] - min(gs) + 1) if gs else 0
                    row = {'X': xn, 'Y': yn, 'LX': LX, 'LY': LY, 'metrics': m, 'need': need, 'interface': nint, 'h': h}
                    if need <= NEED_MAX:
                        if not correct(c): raise SystemExit('BUG %s' % row)
                        (out / 'cands' / (h + '.bfx')).write_text(core.to_kernel(c))
                    if len(rows) < MAX_ROWS: rows.append(row)
        print('X %d/%d %s tried %d distinct %d  %.0f s' % (xi + 1, len(circs), xn[:40], tried, len(seen), time.time() - t0), flush=True)
    rows.sort(key=lambda r: (r['need'], r['metrics'][2]))
    (out / 'splices.json').write_text(json.dumps(rows))
    print('done: tried %d, distinct %d, %.0f s' % (tried, len(seen), time.time() - t0))
    for r in rows[:50]:
        print(r['need'], r['metrics'], r['X'][:36], '<-', r['Y'][:36], 'LX', r['LX'], 'LY', r['LY'], 'if', r['interface'])


if __name__ == '__main__':
    main()
