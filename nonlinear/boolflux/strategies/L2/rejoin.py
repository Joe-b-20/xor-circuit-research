#!/usr/bin/env python3
"""L2 reproducibility check: re-run recorded joins (track E splice2) and compare with the stored circuits.

    python3 rejoin.py
Re-does (a) the first A31 join of sp1 and (b) every join admission of long1/splice and low1/run whose
two parents can be loaded (inputs by file, admitted members by hash), and reports identical / different
kernel text.  Read-only; about 20 s.
"""
import hashlib, json, os, sys, glob
from pathlib import Path
E = Path(os.path.expanduser('~/xcr-boolflux/nonlinear/boolflux/strategies/E'))
sys.path.insert(0, str(E))
from common import core, load, metrics, correct, levels   # noqa: E402
from splice2 import Front, splice   # noqa: E402

B = Path(os.path.expanduser('~/xs-campaigns/2026-11-13-aes/E'))
N = Path(os.path.expanduser('~/xcr-boolflux/nonlinear/nist/aes-sbox'))


def h(c): return hashlib.sha1(core.to_kernel(c).encode()).hexdigest()[:16]


def join(X, LX, Y, LY):
    fr = Front(X, X.tables(), levels(X), LX)
    c, nint = splice(fr, Y, Y.tables(), levels(Y), LY)
    return c, nint


# (a) first A31
X = load(N / 'aes-sbox-a32-ad5-g107-gd22-xx75-4.circ.txt'); Y = load(N / 'aes-sbox-a32-ad4-g117-gd19-xx85-6.circ.txt')
c, nint = join(X, 4, Y, 3)
ref = core.from_kernel((B / 'found' / 'E-splice-a31-ad5-g119-gd20.bfx').read_text(), 'ref')
print('first A31: rebuilt', metrics(c), 'interface', nint, 'correct', correct(c),
      'IDENTICAL' if core.to_kernel(c) == core.to_kernel(ref) else 'DIFFERENT (same tuple: %s)' % (tuple(metrics(c)) == tuple(metrics(ref))))

# (b) joins of long1 / low1
pool = {}
for fl in ('long1/files.list', 'low1/files.list'):
    for f in (B / fl).read_text().split():
        try:
            cc = load(f)
        except Exception:
            continue
        pool.setdefault(h(cc), cc)
adm = {}
for arm in ('long1/splice', 'low1/run'):
    for j in glob.glob(str(B / arm / 'admitted' / '*.json')):
        hh = os.path.basename(j)[:-5]
        cc = core.from_kernel(Path(j[:-5] + '.bfx').read_text(), hh)
        pool.setdefault(hh, cc)
        adm[hh] = (json.load(open(j)), cc, arm)
same = diff = miss = 0
for hh, (d, cc, arm) in sorted(adm.items(), key=lambda kv: tuple(kv[1][0]['metrics'])):
    o = d['origin']
    if o['kind'] != 'splice': continue
    if o['front'] not in pool or o['back'] not in pool:
        miss += 1; print('  parent missing for', d['metrics'], hh); continue
    c2, nint = join(pool[o['front']], o['LX'], pool[o['back']], o['LY'])
    ok = c2 is not None and core.to_kernel(c2) == core.to_kernel(cc)
    same += ok; diff += (not ok)
    if not ok: print('  DIFFERENT', d['metrics'], hh, None if c2 is None else metrics(c2))
print('joins re-run: identical %d, different %d, parent missing %d' % (same, diff, miss))
