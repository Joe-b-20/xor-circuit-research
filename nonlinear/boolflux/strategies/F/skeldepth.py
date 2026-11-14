#!/usr/bin/env python3
"""Depth lower bound of a circuit's AND skeleton (track F).

If every linear form (AND operand, output) is built as its own depth-optimal XOR tree from
its terms' arrival levels (Huffman: combine the two earliest), each AND gets its earliest
possible level.  This is a lower bound on the gate depth of ANY circuit with this skeleton
(same AND functions as affine forms over inputs and earlier ANDs), and it is achievable at
the cost of losing sharing.  Prints the bound and per-region arrival profile.

    python3 skeldepth.py FILE [FILE ...]
"""
import heapq
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core, skeleton   # noqa: E402


def huff(levels, const=False):
    """Minimum depth of an XOR (XNOR if const) of terms with the given arrival levels."""
    if not levels:
        return 0
    if len(levels) == 1:
        return levels[0] + (1 if const else 0)
    h = list(levels); heapq.heapify(h)
    while len(h) > 1:
        a = heapq.heappop(h); b = heapq.heappop(h); heapq.heappush(h, max(a, b) + 1)
    return h[0]


def terms(f, nb):
    return [p for p in range(1, nb) if (f >> p) & 1], bool(f & 1)


def skel_bound(c):
    sk = skeleton.extract(c)
    n = c.n
    ands, outs = sk['ands'], sk['outputs'] if isinstance(sk, dict) else (None, None)
    return sk


def bound(c):
    sk = skeleton.extract(c)
    # sk layout (see skeleton.extract): try dict / tuple
    if isinstance(sk, dict):
        ands = sk["ands"]; outf = sk["outputs"]
    else:
        ands, outf = sk[0], sk[1]
    n = c.n
    nb = 1 + n + len(ands)
    arr = [0] * nb          # basis arrival (index 0 = constant)
    andlv = []
    for k, (L, R) in enumerate(ands):
        tl, cl = terms(L, nb); tr, cr = terms(R, nb)
        dl = huff([arr[p] for p in tl], cl); dr = huff([arr[p] for p in tr], cr)
        arr[1 + n + k] = 1 + max(dl, dr)
        andlv.append(arr[1 + n + k])
    olv = []
    for f in outf:
        t, cst = terms(f, nb)
        olv.append(huff([arr[p] for p in t], cst))
    return andlv, olv, ands, outf


if __name__ == '__main__':
    for f in sys.argv[1:]:
        c = core.read_ncff(f)
        m = c.metrics()
        andlv, olv, ands, outf = bound(c)
        print('%s G=%d A=%d GD=%d: skeleton depth bound %d; outputs %s' % (Path(f).name, m['G'], m['A'], m['GD'], max(olv), olv))
        print('   AND earliest levels:', andlv)
