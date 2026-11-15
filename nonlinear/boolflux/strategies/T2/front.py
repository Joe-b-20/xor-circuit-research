#!/usr/bin/env python3
"""Front subproblem: cut a circuit Y at AND level LY; the front (signals of AND level <= LY) becomes a
stand-alone multi-output circuit whose outputs are Y's cut signals (level <= LY, read above LY).
Report per-cut-signal arrival (gate level in Y) and required time for a gate-depth cap D (backward pass
through Y's back).  `extract` writes the front as .bfx (outputs = cut signals, order fixed) plus a JSON
with the deadlines; `rejoin` puts a (re-optimised) front in front of Y's back via hub/join.join (cut
signals found by truth table, so 0 interface gates when the front computes them exactly) and reports
the metrics.

  front.py extract Y(.bfx|.circ.txt|archive id) LY D OUT_PREFIX [--archive DIR]
  front.py rejoin  Y LY FRONT.bfx OUT.bfx [--archive DIR]
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from boolflux.hub.common import core, metrics, targets  # noqa: E402
from boolflux.hub import join as J  # noqa: E402


def load(x, ar):
    p = Path(x)
    if p.exists(): return core.from_kernel(p.read_text()) if p.suffix == '.bfx' else core.read_ncff(str(p))
    return core.from_kernel((Path(ar) / 'archive' / (x + '.bfx')).read_text())


def cut(c, LY, D):
    n = c.n; S = n + len(c.gates); l = J.levels(c)
    gl = [0] * n
    for op, a, b in c.gates: gl.append(1 + max(gl[a], gl[b]))
    req = [10 ** 9] * S
    for o in c.outputs: req[o] = min(req[o], D)
    for s in range(S - 1, n - 1, -1):
        op, a, b = c.gates[s - n]
        req[a] = min(req[a], req[s] - 1); req[b] = min(req[b], req[s] - 1)
    need = []
    for j, (op, a, b) in enumerate(c.gates):
        if l[n + j] > LY:
            for o in (a, b):
                if o >= n and l[o] <= LY and o not in need: need.append(o)
    for o in c.outputs:
        if o >= n and l[o] <= LY and o not in need: need.append(o)
    return need, gl, req, l


def main():
    a = sys.argv[1:]; ar = None
    if '--archive' in a: i = a.index('--archive'); ar = a[i + 1]; del a[i:i + 2]
    if a[0] == 'extract':
        _, y, LY, D, pre = a; LY = int(LY); D = int(D)
        c = load(y, ar); need, gl, req, l = cut(c, LY, D)
        f = core.Circuit(c.n, len(need), list(c.gates), list(need)).live()
        Path(pre + '.bfx').write_text(core.to_kernel(f))
        info = {'Y': y, 'LY': LY, 'D': D, 'cut': [{'sig': s, 'arrival': gl[s], 'required': req[s]} for s in need],
                'front_metrics': metrics(f), 'Y_metrics': metrics(c)}
        Path(pre + '.json').write_text(json.dumps(info, indent=1))
        print(metrics(c), 'front', metrics(f), 'cut', len(need))
        print('arrival', [gl[s] for s in need]); print('required', [req[s] for s in need])
    else:
        _, y, LY, fr, outp = a; LY = int(LY)
        c = load(y, ar); F = load(fr, ar)
        Y = J.Prepared(c, 'Y'); X = J.Prepared(F, 'F')
        r, nint = J.join(X.front(max(J.levels(F)[F.n:] or [0])), Y, LY)
        if r is None: print('join failed'); return
        assert r.value_table() == targets.aes_sbox()
        Path(outp).write_text(core.to_kernel(r)); print('rejoined', metrics(r), 'interface', nint)


if __name__ == '__main__':
    main()
