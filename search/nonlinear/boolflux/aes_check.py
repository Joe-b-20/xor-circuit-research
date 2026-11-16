#!/usr/bin/env python3
"""Verify AES S-box candidate circuits and place them against the pinned NIST collection.

    python3 search/nonlinear/boolflux/aes_check.py FILE [FILE ...] [--json OUT.json]

Each FILE (NCFF / NIST .circ.txt, or kernel .bfx) is checked by two implementations on all 256
inputs: boolflux.core and the independent verifier (independent/verify.py), whose metrics must
agree. Gate library: NIST {AND, XOR, XNOR, NOT}; G counts every gate including NOT, A counts AND,
GD/AD are gate depth / AND depth; BUF lines (an output that repeats a wire) are free and are not
gates. Then, against every forward AES S-box circuit in search/nonlinear/seeds/ (pin in
search/nonlinear/seeds/MANIFEST.json):
  - dominated: published circuits with all of (A, AD, G, GD) <= the candidate's;
  - new_point: no published circuit has all four <= (Pareto-new on the pinned set);
  - best G at the candidate's GD cap, at its A cap, and at its (A, GD) caps, with the gain.
Exit code 1 if any file fails verification (an unreadable or malformed file is a failure of that
file, not of the whole call); exit code 2 for a usage error.

What the two sides share, and what they do not.  For a .circ.txt file each side
parses the file's bytes with its own reader and evaluates with its own code against its own
S-box table (targets.aes_sbox / verify.aes_sbox).  A kernel .bfx file has only one reader
(core.from_kernel); the independent verifier is given core's NCFF rendering of that circuit, in
memory, so it checks the circuit that core read, and nothing is written to disk.  The published
set's metrics come from the independent verifier alone.
"""
import argparse
import hashlib
import json
import os
import sys
import tempfile
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE
REPO = PKG.parents[2]
sys.path.insert(0, str(PKG / 'independent'))
sys.path.insert(0, str(PKG.parent))
import verify as V                       # noqa: E402
from boolflux import core, targets       # noqa: E402

NIST = PKG.parent / 'seeds'
LIB = {'AND', 'XOR', 'XNOR', 'NOT'}


def published_files():
    return sorted(NIST.glob('aes-sbox/*.circ.txt')) + sorted(NIST.glob('old-2020/aes-sbox-fwd-*.slp')) \
        + sorted(NIST.glob('sbox/aes-sbox-fwd-*'))


def _cache_file(files):
    """Cache of published() keyed by the bytes of every published file and of the verifier that
    measured them, so a hit is the result of the identical computation (without it, the
    exhaustive re-verification of the pinned set is most of the run time of every call).
    BOOLFLUX_NO_CACHE=1 turns it off."""
    if os.environ.get('BOOLFLUX_NO_CACHE'):
        return None
    h = hashlib.sha256(Path(V.__file__).read_bytes())
    for f in files:
        h.update(f.name.encode()); h.update(b'\0'); h.update(f.read_bytes())
    d = Path(os.environ.get('XDG_CACHE_HOME') or (Path.home() / '.cache')) / 'boolflux'
    return d / ('published-%s.json' % h.hexdigest()[:24])


@lru_cache(None)
def published():
    """((A, AD, G, GD), file name) of every pinned forward AES S-box circuit, each verified on all
    256 inputs by the independent verifier."""
    files = published_files()
    cf = _cache_file(files)
    if cf is not None and cf.exists():
        try:
            d = json.loads(cf.read_text())
            if [n for _, n in d] == [f.name for f in files]:
                return tuple((tuple(u), n) for u, n in d)
        except (ValueError, OSError):
            pass
    out = []
    fn = (8, 8, V.aes_sbox())
    for f in files:
        r = V.verify_file(str(f), fn)
        assert r['ok'], f
        m = r['metrics']
        out.append(((m['A'], m['AD'], m['G'], m['GD']), f.name))
    if cf is not None:
        try:                                      # atomic; a failure to cache is not an error
            cf.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=str(cf.parent), prefix='.pub-')
            with os.fdopen(fd, 'w') as fh:
                json.dump(out, fh)
            os.replace(tmp, cf)
        except OSError:
            pass
    return tuple(out)


def load(path):
    """(core circuit, NCFF text for the independent verifier or None = read the file itself)."""
    p = Path(path)
    if p.suffix == '.bfx':
        c = core.from_kernel(p.read_text(), name=p.stem)
        return c, core.write_ncff(c, core.Model.load('nist'))
    return core.read_ncff(str(p)), None


def check(path):
    res = {'file': str(path), 'ok': False, 'core_ok': False, 'independent_ok': False,
           'metrics_agree': False, 'library_ok': False, 'counts': None, 'tuple': None}
    try:
        c, text = load(path)
        if (c.n, c.m) != (8, 8):
            raise ValueError('%d inputs and %d outputs, expected 8 and 8' % (c.n, c.m))
        ok_core = c.value_table() == targets.aes_sbox()
        cm = c.metrics(core.Model.load('nist'))
    except Exception as e:                     # unreadable, malformed, wrong shape: this file fails
        res['errors'] = ['core cannot read the file: %r' % (e,)]
        return res
    fn = (8, 8, V.aes_sbox())
    r = V.verify_text(text, fn) if text is not None else V.verify_file(str(path), fn)
    im = r.get('metrics') or {}
    t = (cm['A'], cm['AD'], cm['G'], cm['GD'])
    ops = set(im.get('counts') or {}) - {'BUF'}     # BUF is not a gate
    core_ops = {core.OPNAME.get(g[0], 'OP%d' % g[0]) for g in c.gates}
    lib_ok = ops <= LIB and core_ops <= LIB
    agree = bool(r['ok']) and all(cm[k] == im.get(k) for k in ('A', 'AD', 'G', 'GD'))
    res.update(core_ok=ok_core, independent_ok=bool(r['ok']), metrics_agree=agree,
               library_ok=lib_ok, counts=im.get('counts'), tuple=t)
    res['ok'] = bool(ok_core and r['ok'] and agree and lib_ok)
    if not res['ok']:
        errs = list(r.get('errors') or [])
        if not ok_core: errs.append('core: the circuit does not compute the AES S-box')
        if r['ok'] and not agree: errs.append('metrics differ: core %s, independent %s' % (
            list(t), [im.get(k) for k in ('A', 'AD', 'G', 'GD')]))
        if not lib_ok: errs.append('gates outside {AND, XOR, XNOR, NOT}: %s' % sorted((ops | core_ops) - LIB))
        res['errors'] = errs
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


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog='aes_check.py', formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Verify AES S-box circuits with two independent implementations on all 256 inputs\n'
                    '(NIST library AND, XOR, XNOR, NOT; every gate counted) and compare their\n'
                    '(A, AD, G, GD) with the pinned NIST collection.',
        epilog='Output per file: OK or FAIL, the tuple "A AD G GD" (#AND, AND depth, #gates, gate depth),\n'
               'whether it is a new Pareto point on the pinned set, and the published best G within\n'
               'the same caps.  Exit status: 0 all files pass, 1 a file fails, 2 usage error.')
    ap.add_argument('files', nargs='+', metavar='FILE', help='NCFF / NIST .circ.txt or .slp, or kernel .bfx')
    ap.add_argument('--json', metavar='OUT.json', help='also write the full result rows as JSON')
    a = ap.parse_args(argv)
    rows = [check(f) for f in a.files]
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
    if a.json:
        Path(a.json).write_text(json.dumps(rows, indent=1) + '\n')
    return 0 if all(r['ok'] for r in rows) else 1


if __name__ == '__main__':
    sys.exit(main())
