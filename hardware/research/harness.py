"""Research harness around the unchanged benchmark (hardware/hwbench).

Nothing here changes a setting of the benchmark: every job is ``hwbench.flow.run_job`` with the
same libraries, constraints, scripts and checks.  What the harness changes, in its own process
only:

* where circuits may come from: candidate files under hardware/research/candidates/ (origin
  ``cand``), and where results go: hardware/research/build/<variant>/ (never hardware/build/);
* for repeated runs only, the sources of noise:
    pnr<s>    the final global placement's parameters drawn around RePlAce's defaults
              (GP_DEFAULTS), ``place_pins -random -random_seed s``, and the instances of the
              mapped netlist in a seeded random order;
    synth<s>  the RTL's gate statements in a seeded random order (what ABC and Yosys see), and
              the pnr<s> changes.
  Seed 0 of either is the benchmark itself (identical files and numbers).
"""
from __future__ import annotations

import pathlib
import random
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from hwbench import design as D, flow as F, verilog as V  # noqa: E402

CAND = HERE / 'candidates'
RBUILD = HERE / 'build'

_origin = D._origin


def origin(path):
    path = pathlib.Path(path).resolve()
    try:
        path.relative_to(CAND)
        return 'cand'
    except ValueError:
        return _origin(path)


D._origin = origin

# RePlAce's defaults in this OpenROAD (2.0-12381); a pnr seed draws the final global placement's
# initial density penalty and wirelength coefficient within +-25% and the target overflow within
# +-30% of them (instance order and pin seeds alone change nothing in this version: the routed
# DEF is byte-identical).
GP_DEFAULTS = {'init_density_penalty': 8e-5, 'init_wirelength_coef': 0.25, 'overflow': 0.1}

_rtl = V.rtl
_synth = F.synth
_PNR = F.PNR_TCL


def shuffled_rtl(seed):
    def rtl(d):
        text = _rtl(d)
        lines = text.splitlines()
        head = [l for l in lines if l.startswith(('//', 'module'))]
        decls, stmts = [], []
        for l in lines:
            m = re.match(r'^  wire (\S+) = (.*);$', l)
            if m:
                decls.append('  wire %s;' % m.group(1))
                stmts.append('  assign %s = %s;' % m.groups())
            elif l.startswith('  assign '):
                stmts.append(l)
        random.Random(seed).shuffle(stmts)
        return '\n'.join(head + ['  // statements in seeded random order (seed %d)' % seed]
                         + decls + stmts + ['endmodule']) + '\n'
    return rtl


_INST = re.compile(r'^  [A-Za-z_\\][^\s(]*\s+[^\s(]+\s*\((?:[^;])*?\);\n', re.M)


def shuffled_synth(seed):
    def synth(d, p, flow, out, lib):
        _synth(d, p, flow, out, lib)
        f = out / 'mapped.v'
        text = f.read_text()
        insts = _INST.findall(text)
        rest = _INST.sub('', text)
        random.Random(seed).shuffle(insts)
        i = rest.rindex('endmodule')
        f.write_text(rest[:i] + ''.join(insts) + rest[i:])
    return synth


def set_variant(variant):
    """Configure this process for a variant: 'base', 'pnr<s>' or 'synth<s>'."""
    F.BUILD = RBUILD / variant
    V.rtl, F.synth, F.PNR_TCL = _rtl, _synth, _PNR
    m = re.fullmatch(r'(pnr|synth)(\d+)', variant)
    if variant == 'base' or (m and m.group(2) == '0'):
        return
    if not m:
        raise ValueError('variant %s' % variant)
    seed = int(m.group(2))
    r = random.Random(seed)
    gp = ('global_placement -density {density} -init_density_penalty %.4g '
          '-init_wirelength_coef %.4g -overflow %.4g'
          % (GP_DEFAULTS['init_density_penalty'] * r.uniform(0.75, 1.25),
             GP_DEFAULTS['init_wirelength_coef'] * r.uniform(0.75, 1.25),
             GP_DEFAULTS['overflow'] * r.uniform(0.7, 1.3)))
    F.PNR_TCL = _PNR.replace('place_pins -random -hor_layers',
                             'place_pins -random -random_seed %d -hor_layers' % seed)
    F.PNR_TCL = F.PNR_TCL.replace('\nglobal_placement -density {density}\n', '\n%s\n' % gp)
    assert F.PNR_TCL.count(gp) == 1
    F.synth = shuffled_synth(seed)
    if m.group(1) == 'synth':
        V.rtl = shuffled_rtl(seed)
