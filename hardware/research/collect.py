#!/usr/bin/env python3
"""Collect the study's data: one row per (circuit, library, flow) with features and results.

    python3 hardware/research/collect.py
    python3 hardware/research/collect.py --stage baseline,base --out build/base-results   # before the repeats

Jobs: exactly those of manifest.py.  The 340 circuits of the benchmark (results read from
hardware/build/, unchanged) and the candidates (hardware/research/build/base/) go to table.csv;
the repeats (stages repeats and balanced: build/pnr<s>, build/synth<s>, build/o<O>p<P>) to
seeds.csv, with their statement order and placement setting.  Before anything is written, every
job of the manifest must have a result whose checks passed (metrics.json exists only then) and
whose fingerprint matches the current code, tools, inputs and, for research jobs, harness and
variant settings; otherwise collect stops with exit status 1 and the published files are left
as they were.  Results on disk that the manifest does not list are not collected.

Columns: circuit features (features.py, from the file), mapped-netlist features (cells, cell
types grouped by function, depth in cells, max fanout, canonical netlist hash), results.
"""
from __future__ import annotations

import collections
import csv
import gzip
import hashlib
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import harness as H  # noqa: E402
import features as FE  # noqa: E402
import inventory as I  # noqa: E402
import manifest as M  # noqa: E402
import bench  # noqa: E402
from hwbench import design as D, flow as F, liberty as L, netlist as N, platforms as P  # noqa: E402

OUT = pathlib.Path(os.environ.get('HWRESEARCH_RESULTS', HERE / 'results'))   # results/, or a staging folder


def netlist_hash_and_depth(nl, lib):
    """Canonical hash of a mapped netlist (cells and connections, names ignored) and its depth
    in cells and max fanout."""
    drv = {}
    for inst in nl.instances:
        c = lib.cells.get(inst.cell)
        if not c:
            continue
        for p in c.outputs:
            n = inst.pins.get(p.name)
            if n:
                drv[n] = (inst, p.name, c)
    alias = dict(nl.assigns)
    memo, dep = {}, {}
    fan = collections.Counter()
    for inst in nl.instances:
        c = lib.cells.get(inst.cell)
        if c:
            for p in c.inputs:
                fan[inst.pins.get(p.name)] += 1

    def h(n):
        if n in memo:
            return memo[n]
        if n in alias:
            r = h(alias[n])
            dep[n] = dep[alias[n]]
        elif n in drv:
            inst, pin, c = drv[n]
            subs = [(p.name, h(inst.pins.get(p.name, '?'))) for p in c.inputs]
            r = hashlib.sha1(('%s.%s(%s)' % (inst.cell, pin, ','.join('%s=%s' % s for s in subs))).encode()).hexdigest()[:16]
            dep[n] = 1 + max([dep.get(inst.pins.get(p.name, '?'), 0) for p in c.inputs] or [0])
        else:
            r = n            # a port or constant
            dep[n] = 0
        memo[n] = r
        return r

    outs = sorted({n for n in list(drv) + list(alias) if n.startswith('y[')},
                  key=lambda s: int(s[2:-1]))
    hs = [h(o) for o in outs]
    for n in drv:
        h(n)
    return (hashlib.sha1('|'.join(hs).encode()).hexdigest()[:16], max(dep[o] for o in outs),
            max(fan.values()) if fan else 0)


def cell_class(name, lib):
    c = lib.cells[name]
    f = c.outputs[0].function.replace(' ', '') if c.outputs else ''
    base = name.split('__')[-1].rsplit('_', 1)[0] if '__' in name else name.rsplit('_', 1)[0]
    if '^' in f or base.startswith(('XOR', 'XNOR', 'xor', 'xnor')):
        return 'xor'
    if base.upper().startswith(('BUF', 'CLKBUF')):
        return 'buf'
    if base.upper().startswith(('INV', 'CLKINV')):
        return 'inv'
    if base.upper().startswith(('AOI', 'OAI', 'A2', 'A3', 'A4', 'O2', 'O3', 'O4', 'A21', 'A22', 'A31',
                                'A32', 'A41', 'A211', 'A221', 'A222', 'O21', 'O22', 'O31', 'O211')):
        return 'complex'
    if base.upper().startswith('MUX'):
        return 'mux'
    if base.upper().startswith(('FA', 'HA', 'MAJ')):
        return 'adder'
    return 'simple'          # AND/NAND/OR/NOR of any width


def designs():
    out = []
    for f in bench.expand(bench.suite('all')):
        out.append((D.load(f), HERE.parent / 'build', 'baseline', None))
    for name in ('sample.json', 'screen.json'):
        if not (HERE / name).exists():
            continue
        for e in json.loads((HERE / name).read_text())['candidates']:
            out.append((D.load(HERE.parents[1] / e['file']), H.RBUILD / 'base', e['part'], e))
    return out


def write_csv(path, rows):
    """Write to a temporary file next to path (renamed by the caller once everything is written)."""
    tmp = path.with_suffix(path.suffix + '.tmp')
    with open(tmp, 'w', newline='') as f:
        w = csv.DictWriter(f, list(rows[0]), lineterminator='\n')
        w.writeheader()
        w.writerows(rows)
    return tmp


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', default=','.join(M.STAGES),
                    help='stages that must be complete (default: all); without the repeats '
                         'stages only table.csv is written')
    ap.add_argument('--out', default=None, help='output folder (default results/)')
    a = ap.parse_args(argv)
    stages = tuple(a.stage.split(','))
    out = pathlib.Path(a.out).resolve() if a.out else OUT
    if not a.out and set(stages) != set(M.STAGES):
        raise SystemExit('collect.py: the default output takes the complete manifest only; give --out for '
                         'stages %s' % ','.join(stages))
    if 'balanced' in stages and 'repeats' not in stages:
        raise SystemExit('collect.py: the balanced stage needs the repeats stage')
    res = M.require(stages)                   # SystemExit(1) when a job is missing or stale
    got = {}
    for j, r in res['ok']:
        got[(j.variant, r['design'], j.platform, j.flow)] = (j, r)
    base_jobs = {k for k, (j, _) in got.items() if j.stage in ('baseline', 'base')}
    models = {pl: FE.lib_models(P.get(pl), P.get(pl).path(P.get(pl).lib).read_text())
              for pl in P.PLATFORMS}
    libs = {pl: L.load(P.get(pl).path(P.get(pl).lib), cache_dir=H.RBUILD / '_liberty')
            for pl in P.PLATFORMS}
    rows = []
    out.mkdir(parents=True, exist_ok=True)
    # duplicates under the folded structure hash (inventory.HASH_VERSION 2): the sample was drawn
    # with version 1, which did not fold constant operands; such candidates are marked and left
    # out of the analyses (dup_of names the circuit they copy)
    first = {}
    ds = designs()
    order = sorted(range(len(ds)), key=lambda i: (ds[i][2] != 'baseline', ds[i][0].id))
    dup_of = {}
    shash = {}
    for i in order:
        d = ds[i][0]
        hsh = I.read_boolean(str(d.path))['hash']
        shash[d.id] = hsh
        k = (d.function, hsh)
        if k in first:
            dup_of[d.id] = first[k]
        else:
            first[k] = d.id
    seen = set()
    for d, build, part, e in ds:
        feat = FE.finite(FE.features(d, models))
        key = (d.metrics['A'], d.metrics['AD'], d.metrics['G'], d.metrics['GD'])
        base = {'circuit': d.id, 'function': d.function, 'origin': d.origin, 'part': part,
                'key': '%d/%d/%d/%d' % key, 'file': d.path.relative_to(D.REPO).as_posix(),
                'provenance': ';'.join(e['provenance']) if e else d.origin,
                'shash': shash[d.id], 'dup_of': dup_of.get(d.id, '')}
        for pl in P.PLATFORMS:
            for fl in F.FLOWS:
                k = (None if part == 'baseline' else 'base', d.id, pl, fl)
                if k not in got:
                    continue                  # not in the manifest (the G >= 400 rule)
                seen.add(k)
                r = got[k][1]
                mf = build / d.id / pl / fl / 'metrics.json'
                nl = N.parse((mf.parent / 'mapped.v').read_text())
                nh, ndep, nfo = netlist_hash_and_depth(nl, libs[pl])
                cls = collections.Counter()
                for c, k in r['cell_types'].items():
                    cls[cell_class(c, libs[pl])] += k
                st = r['stages']
                row = dict(base, platform=pl, flow=fl, **{'f_' + k: v for k, v in feat.items()},
                           cells=r['cells'], m_depth=ndep, m_fo_max=nfo, m_hash=nh,
                           **{'m_' + k: cls.get(k, 0) for k in
                              ('xor', 'simple', 'complex', 'inv', 'buf', 'mux', 'adder')},
                           area=r['area_um2'], delay_synth=st['synth']['delay_ns'],
                           delay_place=st['place']['delay_ns'], delay=r['route']['delay_ns'],
                           adp=r['route']['adp_um2ns'], power=r['route']['power']['total_W'] * 1e6,
                           power_sw=r['route']['power']['switching_W'] * 1e6,
                           wire=r['route']['wirelength_um'], die=r['route']['die_um2'])
                rows.append(row)
    if seen != base_jobs:
        raise SystemExit('manifest jobs of circuits missing from the benchmark suite or '
                         'sample.json/screen.json: %s' % sorted(base_jobs - seen)[:5])
    # repeats, in a fixed order
    srows = []
    for (v, c, pl, fl), (j, r) in sorted(((k, x) for k, x in got.items()
                                          if x[0].stage in ('repeats', 'balanced')),
                                         key=lambda kx: kx[0]):
        o, pp = H.parse_variant(v)
        srows.append({'variant': v, 'statement_order': o, 'placement': pp, 'circuit': c,
                      'platform': pl, 'flow': fl, 'area': r['area_um2'],
                      'delay_synth': r['stages']['synth']['delay_ns'],
                      'delay': r['route']['delay_ns'], 'adp': r['route']['adp_um2ns'],
                      'power': r['route']['power']['total_W'] * 1e6,
                      'wire': r['route']['wirelength_um'], 'cells': r['cells']})
    tmps = [(write_csv(out / 'table.csv', rows), out / 'table.csv')]
    if 'repeats' in stages:
        tmps.append((write_csv(out / 'seeds.csv', srows), out / 'seeds.csv'))
    for tmp, dest in tmps:
        os.replace(tmp, dest)
    print('%d rows, %d duplicate circuits; %d repeat rows' % (len(rows), len(dup_of), len(srows)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
