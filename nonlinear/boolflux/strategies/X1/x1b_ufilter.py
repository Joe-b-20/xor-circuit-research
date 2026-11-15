#!/usr/bin/env python3
"""X1b: U / junk filter for walk outputs (the X3b criterion, strategies/X3/NOTES.md 10.1; logic copied from
strategies/X3/x3b_junk.py, which runs at import time and cannot be imported).

U = V_N + S1-parts of the outputs (H1 xag roles; S1 = level-1-type AND with both operands in aff(x)).
Per circuit: dim U - 9, dim(U cap U_ref) - 9 (ref = NIST a28-ad5-g124), canonical hash of U, rank of the junk
coordinates (c3, c5, c9) on U and of c5 alone, and the exact 9-cover test of U (G eval3.cover_sat, as H1
cond27 R5).  "promising" (can lead to a 27 by the X3b/H1 reading [P]) = U differs from every known U, or the
9-cover test succeeds.

    python3 x1b_ufilter.py FILE...          (table; ref = NIST g124)
"""
import hashlib, sys, tempfile
from pathlib import Path
S = Path.home() / 'xcr-boolflux/nonlinear/boolflux/strategies'
for d in ('G', 'C', 'H1'):
    if str(S / d) not in sys.path: sys.path.insert(0, str(S / d))
import xag
from xag import AFFX, NC, coeff, deps

REF = Path.home() / 'xcr-boolflux/nonlinear/nist/aes-sbox/aes-sbox-a28-ad5-g124-gd27-xx96-26.circ.txt'


def ech(vs):
    b = {}
    for v in vs:
        while v:
            h = v.bit_length() - 1
            if h in b: v ^= b[h]
            else: b[h] = v; break
    return b


def dim(vs): return len(ech(vs))
def capdim(a, b): return dim(a) + dim(b) - dim(list(a) + list(b))
def jc(t): return coeff(t, 3) | (coeff(t, 5) << 8) | (coeff(t, 9) << 16)


def canon(vs):
    b = ech(vs); ks = sorted(b, reverse=True)
    for k in ks:
        for k2 in ks:
            if k2 != k and (b[k2] >> k) & 1: b[k2] ^= b[k]
    return hashlib.sha1(b''.join(b[k].to_bytes(32, 'big') for k in sorted(b))).hexdigest()[:12]


def info_path(f):
    c, ands, outs, otabs = xag.parse(str(f))
    roles = [xag.role(A) for A in ands]
    def part(o, pred):
        t = 0
        for k in deps(o):
            if pred(k): t ^= ands[k]['tab']
        return t
    s1 = [part(o, lambda k: roles[k] == 'S1') for o in outs]
    U = list(AFFX) + list(NC) + s1
    return {'U': U, 's1': s1, 'roles': {r: roles.count(r) for r in set(roles)}}


_ref = None


def ujunk(c=None, path=None, cover=True):
    """c: boolflux Circuit (written to a temp NCFF) or path to an NCFF file"""
    global _ref
    from boolflux import core
    from boolflux.hub.common import MODEL
    if _ref is None: _ref = info_path(REF)
    if path is None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'c.circ.txt'; p.write_text(core.write_ncff(c, MODEL)); r = info_path(p)
    else:
        r = info_path(path)
    out = {'dimU': dim(r['U']) - 9, 'capU_g124': capdim(r['U'], _ref['U']) - 9, 'U': canon(r['U']),
           'jcU': dim([jc(t) for t in r['s1']]), 'c5U': dim([coeff(t, 5) for t in r['s1']]), 'roles': r['roles']}
    if cover:
        import eval3
        b = ech(list(AFFX)); Ub = []
        for t in list(NC) + r['s1']:
            v = t
            while v:
                h = v.bit_length() - 1
                if h in b: v ^= b[h]
                else: b[h] = v; Ub.append(t); break
        try:
            # exact pair enumeration only (9 - dim U <= 2); the SAT branch of cover_sat (9 - dim U >= 3) can stall
            # for minutes, so it is skipped here (None = not tested)
            if len(Ub) > 9: ok = False
            elif 9 - len(Ub) <= 2: ok, pairs = eval3.cover_sat(Ub, 9, 60)
            else: ok = None
        except Exception as e:
            ok = 'error %r' % e
        out['cover9'] = ok
    return out


def ref_U():
    global _ref
    if _ref is None: _ref = info_path(REF)
    return canon(_ref['U'])


if __name__ == '__main__':
    from boolflux.hub.common import load
    print('ref', REF.name, 'U', ref_U())
    for f in sys.argv[1:]:
        try:
            r = ujunk(path=f) if f.endswith('.circ.txt') else ujunk(c=load(f))
        except Exception as e:
            print('%-60s error %r' % (Path(f).name[:60], e)); continue
        print('%-60s dimU %d capU %d U %s jc %d c5 %d cover9 %s roles %s' % (Path(f).name[:60], r['dimU'], r['capU_g124'], r['U'], r['jcU'], r['c5U'], r.get('cover9'), r['roles']))
