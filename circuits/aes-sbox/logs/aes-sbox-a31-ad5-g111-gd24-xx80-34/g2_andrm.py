#!/usr/bin/env python3
"""G2 wrapper of hub/ops/op_andrm.py (frozen snapshot): refuses inputs with A <= 28, so the hub never makes
27-AND circuits by AND removal (campaign rule: no 27-AND work).  Everything else is op_andrm unchanged."""
import importlib.util
import sys
from pathlib import Path

OPS = Path.home() / 'xs-campaigns/2026-11-17-push/G2/snap/search/nonlinear/boolflux/hub/ops'
spec = importlib.util.spec_from_file_location('op_andrm_g2', OPS / 'op_andrm.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
HO = m.HO
_orig = m.op_andrm


def op_andrm_g2(ar, args, rng, out):
    A = m.metrics(ar.circuit(args.inp))[0]
    if A <= 28:
        return [], {'skip': 'G2 wrapper: input A=%d <= 28 (no 27-AND work)' % A}
    return _orig(ar, args, rng, out)


HO.OPS['andrm'] = op_andrm_g2
if __name__ == '__main__':
    sys.exit(HO.main('andrm'))
