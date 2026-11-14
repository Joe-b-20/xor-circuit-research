#!/usr/bin/env python3
"""Verify AES S-box candidate circuits and place them against the pinned NIST collection.

    python3 nonlinear/boolflux/campaigns/aes_check.py FILE [FILE ...] [--json OUT.json]

Each FILE (NCFF / NIST .circ.txt, or kernel .bfx) is checked by two implementations on all 256
inputs: boolflux.core and the independent verifier (independent/verify.py), whose metrics must
agree. Gate library: NIST {AND, XOR, XNOR, NOT}; G counts every gate including NOT, A counts AND,
GD/AD are gate depth / AND depth. Then, against every forward AES S-box circuit in
nonlinear/nist/ (pin in nonlinear/nist/MANIFEST.json):
  - dominated: published circuits with all of (A, AD, G, GD) <= the candidate's;
  - new_point: no published circuit has all four <= (Pareto-new on the pinned set);
  - best G at the candidate's GD cap, at its A cap, and at its (A, GD) caps, with the gain.
Exit code 1 if any file fails verification.
"""
import json
import sys
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
REPO = PKG.parents[1]
sys.path.insert(0, str(PKG / 'independent'))
sys.path.insert(0, str(PKG.parent))
import verify as V                       # noqa: E402
from boolflux import core, targets       # noqa: E402

NIST = REPO / 'nonlinear' / 'nist'
LIB = {'AND', 'XOR', 'XNOR', 'NOT'}


@lru_cache(None)
def published():
    files = sorted(NIST.glob('aes-sbox/*.circ.txt')) + sorted(NIST.glob('old-2020/aes-sbox-fwd-*.slp')) \
        + sorted(NIST.glob('sbox/aes-sbox-fwd-*'))
    out = []
    for f in files:
        r = V.verify_file(str(f), (8, 8, V.aes_sbox()))
        assert r['ok'], f
        m = r['metrics']
        out.append(((m['A'], m['AD'], m['G'], m['GD']), f.name))
    return tuple(out)


def load(path):
    p = Path(path)
    if p.suffix == '.bfx':
        c = core.from_kernel(p.read_text(), name=p.stem)
        tmp = p.with_suffix('.check.circ.txt')
        tmp.write_text(core.write_ncff(c, core.Model.load('nist')))
        return c, tmp
    return core.read_ncff(str(p)), p


def check(path):
    c, f = load(path)
    res = {'file': str(path)}
    ok_core = c.value_table() == targets.aes_sbox()
    r = V.verify_file(str(f), (8, 8, V.aes_sbox()))
    cm = c.metrics(core.Model.load('nist'))
    im = r.get('metrics') or {}
    t = (cm['A'], cm['AD'], cm['G'], cm['GD'])
    ops = set(im.get('counts', {}))
    agree = r['ok'] and all(cm[k] == im.get(k) for k in ('A', 'AD', 'G', 'GD'))
    res.update(core_ok=ok_core, independent_ok=bool(r['ok']), metrics_agree=agree,
               library_ok=ops <= LIB, counts=im.get('counts'), tuple=t)
    res['ok'] = ok_core and r['ok'] and agree and ops <= LIB
    if not res['ok']:
        res['errors'] = r.get('errors') or r.get('mismatch')
        return res
    pub = published()
    A, AD, G, GD = t
    res['dominated_by'] = [n for (u, n) in pub if all(a <= b for a, b in zip(u, t))]
    res['new_point'] = not res['dominated_by']

    def best(pred):
        cands = [(u, n) for (u, n) in pub if pred(u)]
        if not cands:
            return None
        u, n = min(cands, key=lambda x: (x[0][2], x[0]))
        return {'tuple': u, 'file': n, 'gain': u[2] - G}
    res['best_at_gd_cap'] = best(lambda u: u[3] <= GD)
    res['best_at_a_cap'] = best(lambda u: u[0] <= A)
    res['best_at_a_gd_caps'] = best(lambda u: u[0] <= A and u[3] <= GD)
    res['best_at_a_ad_gd_caps'] = best(lambda u: u[0] <= A and u[1] <= AD and u[3] <= GD)
    return res


def main():
    args = [a for a in sys.argv[1:]]
    out = None
    if '--json' in args:
        i = args.index('--json'); out = args[i + 1]; del args[i:i + 2]
    rows = [check(a) for a in args]
    for r in rows:
        if not r['ok']:
            print('FAIL %s: %s' % (r['file'], r.get('errors')))
            continue
        def fmt(b):
            return 'none' if not b else '%s (%s, gain %+d)' % (' '.join(map(str, b['tuple'])), b['file'], b['gain'])
        print('OK   %s  A AD G GD = %s  counts %s' % (r['file'], ' '.join(map(str, r['tuple'])), r['counts']))
        print('     new Pareto point on pinned set: %s%s' % ('YES' if r['new_point'] else 'no',
              '' if r['new_point'] else ' (dominated by %s%s)' % (', '.join(r['dominated_by'][:2]),
                                                                    ' +%d' % (len(r['dominated_by']) - 2) if len(r['dominated_by']) > 2 else '')))
        print('     published best G at GD<=%d: %s' % (r['tuple'][3], fmt(r['best_at_gd_cap'])))
        print('     published best G at A<=%d: %s' % (r['tuple'][0], fmt(r['best_at_a_cap'])))
        print('     published best G at A<=%d, GD<=%d: %s' % (r['tuple'][0], r['tuple'][3], fmt(r['best_at_a_gd_caps'])))
    if out:
        Path(out).write_text(json.dumps(rows, indent=1) + '\n')
    return 0 if all(r['ok'] for r in rows) else 1


if __name__ == '__main__':
    sys.exit(main())
