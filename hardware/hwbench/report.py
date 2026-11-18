"""Results tables from the build folder: results.csv (every job) and RESULTS.md (summary)."""
from __future__ import annotations

import csv
import json
import pathlib

from . import flow as F, pairs as PR, platforms as P

PLAT_NAMES = {'nangate45': 'Nangate45', 'sky130hd': 'SKY130HD'}
FUNC_NAMES = {'aes-sbox': 'S-box', 'aes-invsbox': 'inverse S-box',
              'aes-sbox-sel': 'S-box with direction bit', 'aes-mixcolumns': 'MixColumns',
              'aes-invmixcolumns': 'InvMixColumns'}
FUNC_ORDER = ['aes-invsbox', 'aes-sbox', 'aes-sbox-sel', 'aes-mixcolumns', 'aes-invmixcolumns']

COLUMNS = ['design', 'origin', 'function', 'A', 'AD', 'G', 'GD', 'platform', 'flow', 'cells',
           'area_um2', 'delay_synth_ns', 'delay_place_ns', 'delay_route_ns', 'adp_route_um2ns',
           'power_route_uW', 'power_switching_uW', 'power_internal_uW', 'power_leakage_uW',
           'wirelength_um', 'die_um2', 'drc', 'drv_synth', 'drv_place', 'drv_route',
           'sim_vectors', 'sim_exhaustive', 'file', 'sha256']


def load(build):
    res = {}
    for f in sorted(pathlib.Path(build).glob('*/*/*/metrics.json')):
        r = json.loads(f.read_text())
        res[(r['design'], r['platform'], r['flow'])] = r
    return res


def row(r):
    m, rt, st = r['metrics'], r['route'], r['stages']
    pw = rt['power']
    return {'design': r['design'], 'origin': r['origin'], 'function': r['function'],
            'A': m['A'], 'AD': m['AD'], 'G': m['G'], 'GD': m['GD'], 'platform': r['platform'],
            'flow': r['flow'], 'cells': r['cells'], 'area_um2': r['area_um2'],
            'delay_synth_ns': st['synth']['delay_ns'], 'delay_place_ns': st['place']['delay_ns'],
            'delay_route_ns': rt['delay_ns'], 'adp_route_um2ns': rt['adp_um2ns'],
            'power_route_uW': round(pw['total_W'] * 1e6, 3),
            'power_switching_uW': round(pw['switching_W'] * 1e6, 3),
            'power_internal_uW': round(pw['internal_W'] * 1e6, 3),
            'power_leakage_uW': round(pw['leakage_W'] * 1e6, 4),
            'wirelength_um': rt['wirelength_um'], 'die_um2': rt['die_um2'], 'drc': rt['drc'],
            'drv_synth': st['synth']['drv_violations'], 'drv_place': st['place']['drv_violations'],
            'drv_route': st['route']['drv_violations'],
            'sim_vectors': r['checks']['routed']['sim_vectors'],
            'sim_exhaustive': r['checks']['routed']['sim_exhaustive'],
            'file': r['file'], 'sha256': r['sha256']}


def pct(a, b):
    v = 100.0 * (a - b) / b
    return '%+.1f%%' % v


def bold_if(s, cond):
    return '**%s**' % s if cond else s


def first_pair_table(res, ours_id, nist_id, ours_label, nist_label):
    lines = ['| Library | Flow | Circuit | Cells | Area µm² | Delay ns (synth) | Delay ns (routed) '
             '| ADP µm²·ns (routed) | Power µW (routed) | Wire µm |',
             '|---|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for plat in P.PLATFORMS:
        for fl in F.FLOWS:
            for did, lab in ((nist_id, 'NIST ' + nist_label), (ours_id, 'BoolFlux ' + ours_label)):
                r = res.get((did, plat, fl))
                if not r:
                    continue
                w = row(r)
                lines.append('| %s | %s | %s | %d | %.1f | %.3f | %.3f | %.1f | %.1f | %.0f |' % (
                    PLAT_NAMES[plat], fl, lab, w['cells'], w['area_um2'], w['delay_synth_ns'],
                    w['delay_route_ns'], w['adp_route_um2ns'], w['power_route_uW'],
                    w['wirelength_um']))
    return lines


def pairs_table(res, pairs, plat):
    """One row per pair: area, routed delay and routed ADP change (ours vs NIST) per flow."""
    head = '| Function | NIST | Ours |' + ''.join(' %s area | %s delay | %s ADP |' % (f, f, f)
                                               for f in F.FLOWS)
    lines = [head, '|---|---|---|' + '---:|' * (3 * len(F.FLOWS))]
    wins = {(f, k): [0, 0] for f in F.FLOWS for k in ('area', 'delay', 'adp')}
    for n, o in pairs:
        if o is None:
            continue
        cells = []
        complete = True
        for fl in F.FLOWS:
            rn, ro = res.get((n.id, plat, fl)), res.get((o.id, plat, fl))
            if not rn or not ro:
                complete = False
                cells += ['', '', '']
                continue
            for k, a, b in (('area', ro['area_um2'], rn['area_um2']),
                            ('delay', ro['route']['delay_ns'], rn['route']['delay_ns']),
                            ('adp', ro['route']['adp_um2ns'], rn['route']['adp_um2ns'])):
                cells.append(bold_if(pct(a, b), a < b))
                wins[(fl, k)][0] += a < b
                wins[(fl, k)][1] += 1
        if complete or any(cells):
            lines.append('| %s | %s | %s |%s' % (FUNC_NAMES.get(n.function, n.function), n.label,
                                                 o.label, ''.join(' %s |' % c for c in cells)))
    lines.append('| **ours smaller/faster in** | | |' + ''.join(
        ' %d/%d |' % tuple(wins[(f, k)]) for f in F.FLOWS for k in ('area', 'delay', 'adp')))
    return lines


def changes(res, pairs, plat, fl):
    """Per measure, the relative changes (ours vs NIST) over the pairs with both results."""
    out = {'area': [], 'delay': [], 'adp': [], 'power': []}
    for n, o in pairs:
        rn, ro = (res.get((n.id, plat, fl)), res.get((o.id, plat, fl))) if o else (None, None)
        if not rn or not ro:
            continue
        for k, get in (('area', lambda r: r['area_um2']), ('delay', lambda r: r['route']['delay_ns']),
                       ('adp', lambda r: r['route']['adp_um2ns']),
                       ('power', lambda r: r['route']['power']['total_W'])):
            out[k].append((get(ro) - get(rn)) / get(rn))
    return out


def median(v):
    v = sorted(v)
    n = len(v)
    return (v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2) if v else float('nan')


def summary_table(res, pairs):
    """Per library and flow: pairs where ours is smaller/faster/lower, and the median change."""
    lines = ['| Library | Flow | Pairs | Area: ours smaller | median | Routed delay: ours faster '
             '| median | ADP: ours lower | median | Power: ours lower | median |',
             '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for plat in P.PLATFORMS:
        for fl in F.FLOWS:
            c = changes(res, pairs, plat, fl)
            n = len(c['area'])
            if not n:
                continue
            cells = []
            for k in ('area', 'delay', 'adp', 'power'):
                cells += ['%d' % sum(x < 0 for x in c[k]), '%+.1f%%' % (100 * median(c[k]))]
            lines.append('| %s | %s | %d | %s |' % (PLAT_NAMES[plat], fl, n, ' | '.join(cells)))
    return lines


def best_table(res, designs, plat):
    """Per function and flow: the smallest area, routed delay and routed ADP, ours vs NIST."""
    lines = ['| Function | Flow | Min area µm² NIST | ours | Min delay ns NIST | ours '
             '| Min ADP NIST | ours |', '|---|---|---:|---:|---:|---:|---:|---:|']
    by = {}
    for d in designs:
        by.setdefault((d.function, d.origin), []).append(d)
    for fn in FUNC_ORDER:
        if (fn, 'nist') not in by:
            continue
        for fl in F.FLOWS:
            vals = {}
            for org in ('nist', 'ours'):
                rs = [res[(d.id, plat, fl)] for d in by.get((fn, org), [])
                      if (d.id, plat, fl) in res]
                if not rs:
                    vals[org] = None
                    continue
                vals[org] = (min(rs, key=lambda r: r['area_um2']),
                             min(rs, key=lambda r: r['route']['delay_ns']),
                             min(rs, key=lambda r: r['route']['adp_um2ns']))
            if not vals['nist'] or not vals['ours']:
                continue
            cells = []
            for i, get, fmt in ((0, lambda r: r['area_um2'], '%.1f'),
                                (1, lambda r: r['route']['delay_ns'], '%.3f'),
                                (2, lambda r: r['route']['adp_um2ns'], '%.1f')):
                a, b = get(vals['nist'][i]), get(vals['ours'][i])
                lab = lambda r: label(r)
                cells.append('%s (%s)' % (fmt % a, lab(vals['nist'][i])))
                cells.append(bold_if('%s (%s)' % (fmt % b, lab(vals['ours'][i])), b < a))
            lines.append('| %s | %s | %s |' % (FUNC_NAMES[fn], fl, ' | '.join(cells)))
    return lines


def label(r):
    m = r['metrics']
    if r['kind'] == 'linear':
        return '%d@%d' % (m['G'], m['GD'])
    return '%d/%d/%d/%d' % (m['A'], m['AD'], m['G'], m['GD'])


def electrical(res, prs):
    """Jobs with OpenSTA slew/capacitance/fanout violations (no repair is run), and the pair
    comparisons that involve one."""
    md = ['| Library | Flow | Jobs | after synthesis | after placement | after routing | pairs involving one (routed) |',
          '|---|---|---:|---:|---:|---:|---:|']
    hit = []
    for plat in P.PLATFORMS:
        for fl in F.FLOWS:
            rs = [r for (d, p, f), r in res.items() if p == plat and f == fl]
            c = {st: sum(1 for r in rs if r['stages'][st]['drv_violations']) for st in ('synth', 'place', 'route')}
            np_ = 0
            for n, o in prs:
                if o is None:
                    continue
                bad = [x.label for x in (n, o)
                       if (x.id, plat, fl) in res and res[(x.id, plat, fl)]['stages']['route']['drv_violations']]
                if bad:
                    np_ += 1
                    hit.append('%s %s %s: %s' % (PLAT_NAMES[plat], fl, FUNC_NAMES.get(n.function, n.function),
                                                 ', '.join(bad)))
            md.append('| %s | %s | %d | %d | %d | %d | %d |' % (PLAT_NAMES[plat], fl, len(rs), c['synth'],
                                                               c['place'], c['route'], np_))
    if hit:
        md += ['', 'Pair comparisons with a routed-stage violation: ' + '; '.join(hit) + '.']
    return md


def write(build, out, designs):
    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    res = load(build)
    by_id = {d.id: d for d in designs}
    libsha = {name: P.get(name).lib_sha256() for name in P.PLATFORMS}
    current, stale = {}, 0
    for k, v in res.items():
        d = by_id.get(k[0])
        if d is None:
            continue
        if v.get('fingerprint') != F.fingerprint(d.sha256, k[1], k[2], libsha[k[1]]):
            stale += 1           # made by other code, tools or circuit files: not reported
            continue
        current[k] = v
    res = current
    if stale:
        print('%d results in %s are from other code or inputs and are left out '
              '(bench.py run recomputes them)' % (stale, build))
    missing = len(designs) * len(P.PLATFORMS) * len(F.FLOWS) - len(res)
    if missing:
        print('%d jobs of the suite have no current result' % missing)
    with open(out / 'results.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, COLUMNS, lineterminator='\n')
        w.writeheader()
        for k in sorted(res):
            w.writerow(row(res[k]))
    ours = [d for d in designs if d.origin == 'ours']
    nist = [d for d in designs if d.origin == 'nist']
    prs = PR.pair(ours, nist)
    any_r = next(iter(res.values()))
    s = any_r['settings']
    tools = any_r['tools']
    md = ['# Results', '',
          'Generated by `python3 hardware/bench.py table` from %d jobs (%d circuits, %d libraries, '
          '%d flows). Every number comes from a job whose RTL, mapped and routed netlists passed '
          'simulation (all inputs for the S-boxes; 65,536 random inputs plus the unit vectors for the '
          '32-bit linear maps) and a formal proof of equivalence with the reference function (Yosys '
          'miter, ABC &cec), and whose routing has 0 DRC errors. All rows per job: '
          '[results.csv](results.csv).'
          % (len(res), len({k[0] for k in res}), len({k[1] for k in res}), len({k[2] for k in res})),
          '',
          'Area: standard-cell area of the logic cells (no taps, no input-port buffers). Delay: '
          'worst input-to-output path through a buffer after each input port, inputs driven by '
          'the library\'s X1 buffer, 3.898 fF (Nangate45) or 5 fF (SKY130HD) on each output; '
          '*synth* without wires, *routed* with '
          'OpenRCX parasitics. ADP = area x routed delay. Power: OpenSTA after routing, at %g MHz '
          'with a new random input every cycle and zero-delay switching activity (glitches not '
          'counted), exact for the S-boxes (all inputs) and estimated from the simulated inputs '
          'for the 32-bit linear maps. Typical corner only. Tools: %s; %s; %s.'
          % (1000.0 / s['period_ns'], tools.get('Yosys', 'Yosys')[:11],
             tools.get('openroad', 'OpenROAD'), tools.get('orfs', 'ORFS platforms')),
          '']
    # the first pair
    first = [(n, o) for n, o in prs if o is not None and n.function == 'aes-invsbox'
             and n.metrics['A'] == 45 and n.metrics['G'] == 141]
    if first:
        n, o = first[0]
        md += ['## First pair: inverse S-box, BoolFlux %s vs NIST %s' % (o.label, n.label), '',
               'A/AD/G/GD = #AND / AND depth / #gates / gate depth.', '']
        md += first_pair_table(res, o.id, n.id, o.label, n.label) + ['']
    md += ['## Summary over the pairs', '',
           'Pairs as in the next section. A count is the number of pairs in which ours is smaller, '
           'faster or lower; the median is the median relative change of ours against NIST '
           '(negative: ours smaller, faster or lower). Delay, ADP and power after routing.', '']
    md += summary_table(res, prs) + ['']
    md += ['## Pairs', '',
           'Each NIST circuit on NIST\'s own front (no NIST circuit of the same function is at '
           'least as good in A, AD, G and GD) against the circuit of ours that is at least as good '
           'in all four with the fewest gates (hwbench/pairs.py). Change of ours relative to NIST; '
           'negative (bold) means ours is smaller or faster. Delay and ADP are after routing.', '']
    for plat in P.PLATFORMS:
        md += ['### %s' % PLAT_NAMES[plat], ''] + pairs_table(res, prs, plat) + ['']
    unpaired = [n for n, o in prs if o is None]
    if unpaired:
        md += ['NIST front circuits with no circuit of ours at least as good in all four metrics '
               '(not compared): ' + ', '.join('%s %s' % (FUNC_NAMES.get(n.function, n.function),
                                                         n.label) for n in unpaired) + '.', '']
    md += ['## Electrical checks', '',
           'Jobs whose OpenSTA report (`report_check_types -max_slew -max_capacitance -max_fanout '
           '-violators`) lists a violation of the Liberty limits. These are not routing DRC errors '
           '(0 in every job). The flow repairs nothing: the numbers above are those of the '
           'netlists as synthesized, violations included. Per job and stage: the drv_* columns of '
           'results.csv; by type, and for the research study: '
           '[research/results/ELECTRICAL.md](../research/results/ELECTRICAL.md).', '']
    md += electrical(res, prs) + ['']
    md += ['## Best of each set', '',
           'Over all circuits of each set (every published circuit of ours, every NIST circuit in '
           'this repository): the smallest area, routed delay and routed ADP, with the circuit '
           'that has it.', '']
    for plat in P.PLATFORMS:
        md += ['### %s' % PLAT_NAMES[plat], ''] + best_table(res, designs, plat) + ['']
    (out / 'RESULTS.md').write_text('\n'.join(md))
    print('wrote %s and %s (%d jobs)' % (out / 'RESULTS.md', out / 'results.csv', len(res)))
