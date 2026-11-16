"""Inverse-S-box shim for the 2026-11-16 invsbox campaign (agent SX).  NOT part of the repository.

BoolFlux's AES helpers that the hub and the ops scripts use (aes_check.py, hub/common.py,
ops/common.py, conj_lib) are written for the FORWARD AES S-box: they call
``boolflux.targets.aes_sbox()`` (verifier 1), ``verify.aes_sbox()`` (verifier 2, independent/verify.py)
and ``aes_check.published_files()`` (the pinned NIST set used for placement).  The gate kernel itself is
function-agnostic (it keeps the function of its start).

install() rebinds, in this process only, before any of those modules computes a table:
  boolflux.targets.aes_sbox  -> boolflux.targets.aes_inv_sbox's table (computed first, from its own forward table)
  verify.aes_sbox            -> verify.aes_inv_sbox's table (independent/verify.py's own FIPS-197 code)
  aes_check.published_files  -> the pinned NIST INVERSE circuits: seeds/aes-invsbox/*.circ.txt,
                                seeds/old-2020/aes-sbox-rev-*.slp, seeds/sbox/aes-sbox-inv-*
so every "is this the AES S-box" check in those modules becomes "is this the AES inverse S-box", still
by two implementations that share no code, on all 256 inputs.  No repository file is changed.

sitecustomize.py (same folder) calls install() when XS_INVSBOX=1, so hub operator subprocesses get it too.
"""
import os
import sys
from pathlib import Path

REPO = Path(os.environ.get('XCR_REPO', str(Path.home() / 'xcr-boolflux')))
NL = REPO / 'search' / 'nonlinear'
PKG = NL / 'boolflux'
SEEDS = NL / 'seeds'
INSTALLED = False
FWD = {}


def inverse_published_files():
    return sorted(SEEDS.glob('aes-invsbox/*.circ.txt')) + sorted(SEEDS.glob('old-2020/aes-sbox-rev-*.slp')) \
        + sorted(SEEDS.glob('sbox/aes-sbox-inv-*'))


def install():
    global INSTALLED
    if INSTALLED:
        return
    for p in (str(NL), str(PKG / 'independent')):
        if p not in sys.path:
            sys.path.append(p)
    from boolflux import targets
    import verify as V
    t_inv = tuple(targets.aes_inv_sbox())          # computed from the unpatched forward table
    v_inv = tuple(V.aes_inv_sbox())
    assert t_inv == v_inv, 'the two inverse tables differ'
    assert t_inv[0x63] == 0 and t_inv[0] == 0x52 and t_inv[0x7c] == 1, 'FIPS-197 inverse S-box spot check failed'
    FWD['targets'] = targets.aes_sbox
    FWD['verify'] = V.aes_sbox
    targets.aes_sbox = lambda: list(t_inv)
    V.aes_sbox = lambda: list(v_inv)
    # FIPS-197 order kept; the patched names are what aes_check / hub / ops call at run time
    sys.path.insert(0, str(PKG))
    try:
        import aes_check
    finally:
        sys.path.remove(str(PKG))
    aes_check.published_files = inverse_published_files
    aes_check.published.cache_clear()
    INSTALLED = True
    os.environ['XS_INVSBOX_ACTIVE'] = '1'


def forward_targets_sbox():
    """The original forward table function (needed to import conj_lib/conj.py, whose import-time
    assertion checks the forward decomposition S = A inv + 0x63)."""
    return FWD['targets']


def install_line_rule():
    """Hub admission rule of this campaign (scheduler process only, XS_INVSBOX_LINE=1): a circuit made by an
    operator is admitted only if its (A, AD) is <= the (A, AD) of some start of its lineage (a NIST seed, or
    the start recorded in the sidecar of an ingested conjugation circuit).  Without it, pulls that lower AD
    (A kept only as a kernel cap the repair may miss) or GD (AD free) admit circuits above every start of
    their line."""
    from boolflux.hub import archive as HA
    from boolflux.hub.common import clean, metrics
    if getattr(HA.Archive.admit, '_line_rule', False):
        return
    orig = HA.Archive.admit

    def roots(ar, i, memo):
        if i in memo:
            return memo[i]
        memo[i] = set()
        r = ar.rec.get(i)
        out = set()
        if r is None:
            pass
        elif r.get('operator') == 'seed':
            out.add((r['A'], r['AD']))
        elif r.get('operator') == 'ingest':
            st = ((((r.get('operator_settings') or {}).get('sidecar') or {}).get('start')) or {}).get('tuple')
            if st:
                out.add((st[0], st[1]))
        else:
            for p in r.get('parents') or []:
                out |= roots(ar, p, memo)
        memo[i] = out
        return out

    def admit(self, c, parents=(), operator='seed', *args, **kw):
        if operator not in ('seed', 'ingest') and parents:
            try:
                m = metrics(clean(c))
            except Exception:
                return orig(self, c, parents, operator, *args, **kw)
            memo = self.__dict__.setdefault('_line_memo', {})
            rs = set()
            for p in parents:
                rs |= roots(self, p, memo)
            if rs and not any(m[0] <= A and m[1] <= AD for A, AD in rs):
                return ('rejected: line rule, A/AD %d/%d above every start of its lineage %s'
                        % (m[0], m[1], sorted(rs))), None, 0.0
        return orig(self, c, parents, operator, *args, **kw)
    admit._line_rule = True
    HA.Archive.admit = admit
