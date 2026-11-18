"""Research harness around the unchanged benchmark (hardware/hwbench).

Nothing here changes a setting of the benchmark: every job is ``hwbench.flow.run_job`` with the
same libraries, constraints, scripts and checks.  What the harness changes, in its own process
only:

* where circuits may come from: candidate files under hardware/research/candidates/ (origin
  ``cand``), and where results go: hardware/research/build/<variant>/ (never hardware/build/);
* for repeated runs only, two sources of noise, each with its own seed:
    statement order O   the RTL's gate statements in a seeded random order (what Yosys and ABC
                        see); O = 0 is the benchmark's RTL;
    placement P         the final global placement's parameters drawn around RePlAce's defaults
                        (GP_DEFAULTS), ``place_pins -random -random_seed P``, and the instances of
                        the mapped netlist in a seeded random order; P = 0 is the benchmark's flow;
* the fingerprints of its jobs: the benchmark's fingerprint (its code, the tool versions, the
  circuit, the library) extended by this file's SHA-256 and the variant's effective settings, so
  a result is reused only by the harness and settings that produced it.

Variants (folder names):
    base        O = 0, P = 0: the benchmark itself (identical files and numbers)
    pnr<s>      O = 0, P = s
    synth<s>    O = s, P = s
    o<O>p<P>    any other pair (the balanced repeats); a pair that has one of the names above
                uses that name and folder, so o0p2 is pnr2 and o1p1 is synth1
"""
from __future__ import annotations

import datetime
import hashlib
import json
import pathlib
import random
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from hwbench import design as D, flow as F, platforms as P, verilog as V  # noqa: E402

CAND = HERE / 'candidates'
RBUILD = HERE / 'build'
HARNESS_SHA256 = hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()

_origin = D._origin


def origin(path):
    path = pathlib.Path(path).resolve()
    try:
        path.relative_to(CAND)
        return 'cand'
    except ValueError:
        return _origin(path)


D._origin = origin

# RePlAce's defaults in this OpenROAD (2.0-12381); a placement seed draws the final global
# placement's initial density penalty and wirelength coefficient within +-25% and the target
# overflow within +-30% of them (instance order and pin seeds alone change nothing in this
# version: the routed DEF is byte-identical).
GP_DEFAULTS = {'init_density_penalty': 8e-5, 'init_wirelength_coef': 0.25, 'overflow': 0.1}

_rtl = V.rtl
_synth = F.synth
_PNR = F.PNR_TCL
_fingerprint = F.fingerprint
_run_job = F.run_job


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


def parse_variant(variant):
    """(statement order O, placement P) of a variant name."""
    if variant == 'base':
        return 0, 0
    m = re.fullmatch(r'(pnr|synth)(\d+)', variant)
    if m:
        s = int(m.group(2))
        return (0, s) if m.group(1) == 'pnr' else (s, s)
    m = re.fullmatch(r'o(\d+)p(\d+)', variant)
    if m:
        return int(m.group(1)), int(m.group(2))
    raise ValueError('variant %r (base, pnr<s>, synth<s> or o<O>p<P>)' % variant)


def variant_name(order, place):
    """The folder name of (O, P): base, pnr<P>, synth<O> or o<O>p<P>."""
    if order == 0:
        return 'base' if place == 0 else 'pnr%d' % place
    return 'synth%d' % order if order == place else 'o%dp%d' % (order, place)


def canonical(variant):
    return variant_name(*parse_variant(variant))


def gp_command(place):
    r = random.Random(place)
    return ('global_placement -density {density} -init_density_penalty %.4g '
            '-init_wirelength_coef %.4g -overflow %.4g'
            % (GP_DEFAULTS['init_density_penalty'] * r.uniform(0.75, 1.25),
               GP_DEFAULTS['init_wirelength_coef'] * r.uniform(0.75, 1.25),
               GP_DEFAULTS['overflow'] * r.uniform(0.7, 1.3)))


def pnr_tcl(place):
    """The OpenROAD script template of placement setting P (P = 0: the benchmark's)."""
    if place == 0:
        return _PNR
    gp = gp_command(place)
    t = _PNR.replace('place_pins -random -hor_layers',
                     'place_pins -random -random_seed %d -hor_layers' % place)
    t = t.replace('\nglobal_placement -density {density}\n', '\n%s\n' % gp)
    assert t.count(gp) == 1 and t.count('-random_seed %d' % place) == 1
    return t


def settings(variant):
    """The effective settings of a variant: what its jobs' fingerprints and records contain."""
    order, place = parse_variant(variant)
    return {'variant': variant_name(order, place), 'statement_order': order, 'placement': place,
            'rtl': 'benchmark' if order == 0 else 'statements shuffled, seed %d' % order,
            'global_placement': gp_command(place) if place else 'benchmark',
            'place_pins_seed': place or None, 'instance_order_seed': place or None,
            'pnr_tcl_sha256': hashlib.sha256(pnr_tcl(place).encode()).hexdigest()}


def bench_fingerprint(*parts):
    """The benchmark's own fingerprint (hardware/build, and research results before 2026-11-18)."""
    return _fingerprint(*parts)


def job_fingerprint(variant, *parts):
    """The fingerprint of a research job (or its RTL check, parts = (sha256,)) of a variant."""
    return _fingerprint(*parts, 'research-harness', HARNESS_SHA256,
                        json.dumps(settings(variant), sort_keys=True))


_current = None


def set_variant(variant):
    """Configure this process for a variant (see the module docstring)."""
    global _current
    order, place = parse_variant(variant)
    name = variant_name(order, place)
    F.BUILD = RBUILD / name
    V.rtl = shuffled_rtl(order) if order else _rtl
    F.synth = shuffled_synth(place) if place else _synth
    F.PNR_TCL = pnr_tcl(place)
    F.fingerprint = lambda *parts: job_fingerprint(name, *parts)
    _current = name
    return name


def record(variant, **extra):
    """The provenance block written into a research job's metrics.json."""
    return dict({'settings': settings(variant), 'harness_sha256': HARNESS_SHA256}, **extra)


def run_job(path, platform, flow, variant):
    """hwbench.flow.run_job under a variant; adds the research record to metrics.json."""
    name = set_variant(variant)
    r = _run_job(path, platform, flow)
    if 'research' not in r:
        r['research'] = record(name, run=datetime.datetime.now(datetime.timezone.utc)
                               .strftime('%Y-%m-%dT%H:%M:%SZ'))
        mf = F.job_dir(D.load(path), platform, flow) / 'metrics.json'
        mf.write_text(json.dumps(r, indent=1, sort_keys=True) + '\n')
    return r


def prepare_design(path, variant):
    set_variant(variant)
    return F.prepare_design(path)


def lib_sha(platform, _cache={}):
    if platform not in _cache:
        _cache[platform] = P.get(platform).lib_sha256()
    return _cache[platform]
