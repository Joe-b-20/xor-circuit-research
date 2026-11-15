#!/usr/bin/env python3
"""P2: build a circuit from a front (a circuit whose AND-level < 4 part is kept) and a rank-1
bottom decomposition [(alpha, g, w), ...] (model M): skeleton -> T4 depthsynth (Huffman trees,
meets the skeleton depth bound), optionally reusing the front circuit's gates (--parent).

    python3 build.py FRONT DEC.json[:INDEX] OUT.circ.txt [--parent]
DEC.json: a fwalk/orbsearch JSONL line or JSON with key 'dec' (or a list of solutions).
"""
import json
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / 'T4')); sys.path.insert(0, str(HERE.parents[2]))
import bil    # noqa: E402
import ylev   # noqa: E402
import orbit as O   # noqa: E402
import depthsynth   # noqa: E402
from boolflux import core, targets   # noqa: E402


def skeleton_for(c, dec):
    F = ylev.front(c); n = c.n; sk = F['sk']; fr = F['front_idx']
    remap = {0: 0}
    for i in range(n): remap[1 + i] = 1 + i
    for r, k in enumerate(fr): remap[1 + n + k] = 1 + n + r

    def rm(m):
        out = 0; p = 0
        while m:
            if m & 1:
                if p not in remap: raise ValueError('form uses a non-front AND')
                out |= 1 << remap[p]
            m >>= 1; p += 1
        return out
    ands = [(rm(sk['ands'][k][0]), rm(sk['ands'][k][1])) for k in fr]
    nf = len(fr)
    yform = {}
    for v in range(1, 16):
        lv, m, pol = F['levels'][v]
        yform[bil.ALPHA[v]] = rm(m) ^ (1 if pol else 0)
    outs = [0] * 8
    for j, (al, g, w) in enumerate(dec):
        R = 0
        for q in range(8):
            if g & bil.GMASK[q]: R |= 1 << (1 + q)
        ands.append((yform[al], R))
        lv = O.lvec(w)
        for k in range(8):
            if (lv >> (7 - k)) & 1: outs[k] |= 1 << (1 + n + nf + j)
    for k in range(8):
        if (0x63 >> (7 - k)) & 1: outs[k] |= 1
    return {'ands': ands, 'outputs': outs}


def build(front_file, dec, parent=False):
    c = ylev.load(front_file)
    sk = skeleton_for(c, dec)
    out = depthsynth.synth(sk, parent=c if parent else None)
    if tuple(out.value_table()) != tuple(targets.aes_sbox()):
        # constants: try flipping output constants where needed
        raise RuntimeError('wrong function')
    return out


def load_dec(spec):
    path, _, idx = spec.partition(':')
    txt = Path(path).read_text().strip()
    if path.endswith('.jsonl'):
        lines = [json.loads(l) for l in txt.splitlines() if l.strip()]
        return [tuple(p) for p in lines[int(idx or 0)]['dec']]
    d = json.loads(txt)
    if isinstance(d, dict): return [tuple(p) for p in d['dec']]
    return [tuple(p) for p in d[int(idx or 0)]['dec']]


if __name__ == '__main__':
    front, spec, outp = sys.argv[1:4]
    par = '--parent' in sys.argv
    if spec == 'self':
        dec = O.extract(ylev.load(front))
    else:
        dec = load_dec(spec)
    assert O.check(dec), 'decomposition fails the tensor identity'
    c = build(front, dec, par)
    model = core.Model.load('nist'); m = c.metrics(model)
    print(json.dumps({k: m[k] for k in ('A', 'AD', 'G', 'GD')}))
    Path(outp).write_text(core.write_ncff(c, model, comments=['P2 build.py front %s dec %s parent %s' % (front, spec, par)]))
