#!/usr/bin/env python3
"""Electrical design-rule checks of every job: max slew, max capacitance, max fanout.

hwbench/flow.py has OpenSTA write ``report_check_types -max_slew -max_capacitance -max_fanout
-violators`` after synthesis, placement and routing (``synth/place/route.drv.rpt``) and stores only
a count in metrics.json (``stages.<stage>.drv_violations``).  This script parses those reports for
every job of the benchmark (hardware/build/) and of every variant of the study
(hardware/research/build/<variant>/), cross-checks the counts against metrics.json, and checks the
jobs that the highlighted comparisons rely on.

These are STA checks of pin slews, net loads and fanouts against the Liberty limits.  They are not
routing DRC: detailed routing's design-rule count is read from metrics.json (``route.drc``) and is
0 for every reported job.  No buffering, sizing or repair is run in the flow, so any violation is
what synthesis (or the circuit itself, in the preserve flow) produced.

The parser is strict: a line it does not recognise raises ReportError.

Jobs: the study's manifest (manifest.py, M.jobs() and M.metrics_file()); folders outside it are
never read, and manifest jobs without metrics.json are left out (and counted).  The delay
inversions use analyze.py's own functions (read only).

Outputs (results/): electrical.csv (one row per build, design, platform, flow and stage whose
report has at least one violation), electrical.json and ELECTRICAL.md (counts over every job,
including those without violations; the claim checks).

    python3 hardware/research/electrical.py
"""
from __future__ import annotations

import collections
import csv
import json
import os
import pathlib
import re
import statistics
import sys

HERE = pathlib.Path(__file__).resolve().parent
HW = HERE.parent
sys.path.insert(0, str(HW))
sys.path.insert(0, str(HERE))
from hwbench import netlist as N, pairs as PR, platforms as P  # noqa: E402
import analyze as AN  # noqa: E402  (read-only use of its definitions)
import manifest as M  # noqa: E402

RES = pathlib.Path(os.environ.get('HWRESEARCH_RESULTS', HERE / 'results'))   # results/, or a staging folder
STAGES = ('synth', 'place', 'route')
FLOWS = ('preserve', 'free', 'free-area')
PLATS = ('nangate45', 'sky130hd')
CHECKS = ('slew', 'cap', 'fanout')
CAP_UNIT = {'nangate45': 'fF', 'sky130hd': 'pF'}
BIG_G = 400


class ReportError(ValueError):
    pass


# ---- the report ----------------------------------------------------------------------------

SECTIONS = {'max slew': ('slew', 'Slew'), 'max capacitance': ('cap', 'Cap'),
            'max fanout': ('fanout', 'Fanout')}
NUM = r'(-?\d+(?:\.\d+)?)'
ROW = re.compile(r'^(\S+)\s+%s\s+%s\s+%s \(VIOLATED\)$' % (NUM, NUM, NUM))
HEAD = re.compile(r'^Pin\s+Limit\s+(\w+)\s+Slack$')
DASH = re.compile(r'^-{20,}$')
ROUND = 0.015 + 1e-9      # three numbers printed to 0.01: limit - value - slack within 0.015


def count_drv(text):
    """flow.py's count: occurrences of VIOLATED."""
    return len(re.findall(r'\(VIOLATED\)|VIOLATED', text))


def parse_drv(text, path='?'):
    """{check: [(pin, limit, value, slack)]} of one report; raises ReportError on anything else.

    Format (OpenSTA, this build): per violated check a title line ('max slew', 'max capacitance',
    'max fanout'), a blank line, a header 'Pin Limit <Slew|Cap|Fanout> Slack', a dashed line, one
    row per violating pin ending in '(VIOLATED)', a blank line.  An empty file: no violation."""
    out = {}
    cur, state = None, None
    for i, line in enumerate(text.split('\n'), 1):
        s = line.rstrip()

        def bad(why):
            raise ReportError('%s:%d: %s: %r' % (path, i, why, line))
        if state is None:
            if not s:
                continue
            if s not in SECTIONS:
                bad('unrecognised line outside a section')
            cur = SECTIONS[s][0]
            if cur in out:
                bad('section repeated')
            out[cur] = []
            state = 'title'
        elif state == 'title':
            if not s:
                continue
            m = HEAD.match(s)
            if not m or m.group(1) != SECTIONS[[k for k, v in SECTIONS.items() if v[0] == cur][0]][1]:
                bad('expected the column header of %s' % cur)
            state = 'head'
        elif state == 'head':
            if not DASH.match(s):
                bad('expected a dashed line')
            state = 'rows'
        elif state == 'rows':
            if not s:
                if not out[cur]:
                    bad('section without rows')
                state = None
                continue
            m = ROW.match(s)
            if not m:
                bad('unrecognised row')
            pin = m.group(1)
            lim, val, slk = (float(m.group(k)) for k in (2, 3, 4))
            if slk > 0 or abs(lim - val - slk) > ROUND:
                bad('slack inconsistent with limit and value')
            out[cur].append((pin, lim, val, slk))
    if state not in (None, 'rows') or (state == 'rows' and not out[cur]):
        raise ReportError('%s: report ends inside a section' % path)
    n = sum(len(v) for v in out.values())
    if n != count_drv(text):
        raise ReportError('%s: %d rows parsed, %d VIOLATED in the text' % (path, n, count_drv(text)))
    return out


PATH_PIN = re.compile(r'\s[\^v] (\S+) \(([^()]+)\)$')


def worst_path_pins(text):
    """Pins on the reported worst path (report_checks -path_delay max), in order."""
    return [m.group(1) for m in map(PATH_PIN.search, text.split('\n')) if m]


# ---- Liberty table edges -------------------------------------------------------------------

def _blocks(text, kind, names=None):
    """(name, body) of each ``kind (name) { ... }`` group in text (only ``names`` if given)."""
    out = []
    for m in re.finditer(r'\b%s\s*\(\s*"?([^")]+)"?\s*\)\s*\{' % kind, text):
        if names is not None and m.group(1).strip() not in names:
            continue
        depth, j = 1, m.end()
        while depth:
            c = text[j]
            depth += c == '{'
            depth -= c == '}'
            j += 1
        out.append((m.group(1).strip(), text[m.end():j - 1]))
    return out


def _floats(s):
    return [float(x) for x in s.replace('\\\n', ' ').replace('"', '').split(',') if x.strip()]


def table_edges(lib_path, cells):
    """{cell: {'slew_in': max input-transition index of its delay tables,
               'load': {out pin: max load index}, 'max_cap': {pin: limit}, 'max_tran': {pin: limit}}}.

    Both libraries index cell_rise/fall and rise/fall_transition by (input transition,
    total output net capacitance)."""
    text = pathlib.Path(lib_path).read_text()
    out = {}
    for name, body in _blocks(text, 'cell', set(cells)):
        e ={'slew_in': 0.0, 'load': {}, 'max_cap': {}, 'max_tran': {}}
        for pin, pb in _blocks(body, 'pin'):
            mc = re.search(r'max_capacitance\s*:\s*([\d.eE+-]+)', pb)
            mt = re.search(r'max_transition\s*:\s*([\d.eE+-]+)', pb)
            if mc:
                e['max_cap'][pin] = float(mc.group(1))
            if mt:
                e['max_tran'][pin] = float(mt.group(1))
            i1 = [max(_floats(x)) for x in re.findall(r'index_1\s*\(\s*"([^"]*)"', pb)]
            i2 = [max(_floats(x)) for x in re.findall(r'index_2\s*\(\s*"([^"]*)"', pb)]
            if i2:
                e['load'][pin] = max(i2)
            if i1:
                e['slew_in'] = max(e['slew_in'], max(i1))
        out[name] = e
    return out


# ---- jobs ----------------------------------------------------------------------------------

def build_name(job):
    return 'bench' if job.variant is None else 'research/' + job.variant


def manifest_jobs():
    """(build name, job folder, job) of every job of the study's manifest (manifest.py), which
    lists the benchmark's jobs (hardware/build/) and the research variants' (build/<variant>/);
    folders outside it (build/_revalidate, build/timing, superseded runs) are never read."""
    designs, out = {}, []
    for j in M.jobs():
        d = designs.get(j.file) or designs.setdefault(j.file, j.design())
        out.append((build_name(j), M.metrics_file(j, d).parent, j))
    return out


def stat(v):
    return None if v is None else round(v, 4)


def collect():
    rows, incomplete, mismatches, nreports = [], [], [], 0
    viol_cells = {p: set() for p in PLATS}
    pending = []                     # (row, violations, cells of pins) for the edge check
    for bname, jd, job in manifest_jobs():
        if True:
            design, plat, flow = jd.parent.parent.name, jd.parent.name, jd.name
            mfile = jd / 'metrics.json'
            reps = {st: jd / ('%s.drv.rpt' % st) for st in STAGES}
            if not mfile.exists():   # not finished (or never run): left out
                present = [st for st, f in reps.items() if f.exists()]
                for st in present:   # parsed too, so the parser sees every report
                    parse_drv(reps[st].read_text(), reps[st])
                    nreports += 1
                incomplete.append({'build': bname, 'design': design, 'platform': plat,
                                   'flow': flow, 'reports': present, 'folder': jd.exists()})
                continue
            m = json.loads(mfile.read_text())
            drc_rpt = jd / 'route_drc.rpt'
            drc_bytes = drc_rpt.stat().st_size if drc_rpt.exists() else None
            pin_net, pin_cell = None, None
            for st in STAGES:
                text = reps[st].read_text()
                nreports += 1
                v = parse_drv(text, reps[st])
                nviol = sum(len(x) for x in v.values())
                want = m['stages'][st]['drv_violations']
                if nviol != want or count_drv(text) != want:
                    mismatches.append({'build': bname, 'design': design, 'platform': plat,
                                       'flow': flow, 'stage': st, 'parsed': nviol,
                                       'metrics': want})
                r = {'build': bname, 'design': design, 'origin': m['origin'],
                     'function': m['function'], 'A': m['metrics']['A'], 'AD': m['metrics']['AD'],
                     'G': m['metrics']['G'], 'GD': m['metrics']['GD'],
                     'size': 'G<400' if m['metrics']['G'] < BIG_G else 'G>=400',
                     'platform': plat, 'flow': flow, 'stage': st, 'cap_unit': CAP_UNIT[plat],
                     'delay_ns': m['stages'][st]['delay_ns'], 'cells': m['cells'],
                     'viol_total': nviol, 'metrics_drv': want,
                     'route_drc': m['route']['drc'], 'route_drc_rpt_bytes': drc_bytes}
                crit = []
                if nviol:
                    if pin_net is None:
                        nl = N.parse((jd / 'routed.v').read_text())
                        pin_net = {'%s/%s' % (i.name, p): n for i in nl.instances
                                   for p, n in i.pins.items()}
                        pin_cell = {'%s/%s' % (i.name, p): i.cell for i in nl.instances
                                    for p in i.pins}
                    crit = worst_path_pins((jd / ('%s.timing.rpt' % st)).read_text())
                cset = set(crit)
                cnets = {pin_net.get(p, p) for p in crit} if nviol else set()
                worst_crit = None
                for c in CHECKS:
                    lst = v.get(c, [])
                    r[c + '_pins'] = len(lst)
                    r[c + '_nets'] = len({pin_net.get(p, p) for p, *_ in lst}) if lst else 0
                    if lst:
                        w = min(lst, key=lambda x: (x[3], -x[2]))
                        r[c + '_worst_pin'], r[c + '_worst_limit'] = w[0], w[1]
                        r[c + '_worst_value'], r[c + '_worst_slack'] = w[2], w[3]
                        r[c + '_worst_ratio'] = stat(w[2] / w[1]) if w[1] > 0 else None
                    else:
                        for k in ('pin', 'limit', 'value', 'slack', 'ratio'):
                            r['%s_worst_%s' % (c, k)] = None
                    on = [x for x in lst if x[0] in cset or pin_net.get(x[0], x[0]) in cnets]
                    r[c + '_on_worst_path'] = len(on)
                    for x in on:
                        if x[1] > 0:
                            q = x[2] / x[1]
                            worst_crit = q if worst_crit is None else max(worst_crit, q)
                r['on_worst_path'] = sum(r[c + '_on_worst_path'] for c in CHECKS)
                r['worst_path_ratio'] = stat(worst_crit)
                if nviol:
                    cells = {p: pin_cell.get(p) for lst in v.values() for p, *_ in lst}
                    viol_cells[plat].update(c for c in cells.values() if c)
                    pending.append((r, v, cells))
                rows.append(r)
    # beyond the Liberty tables? (the limit may lie inside or at the edge of the tables)
    edges = {p: table_edges(P.get(p).path(P.get(p).lib), viol_cells[p]) for p in PLATS}
    for r, v, cells in pending:
        e = edges[r['platform']]
        xs = 0
        for c, lst in v.items():
            for pin, lim, val, slk in lst:
                ce = e.get(cells.get(pin))
                if ce is None:      # a port
                    continue
                pname = pin.rsplit('/', 1)[1]
                if c == 'cap' and val > ce['load'].get(pname, float('inf')):
                    xs += 1
                elif c == 'slew' and pname not in ce['load'] and val > ce['slew_in']:
                    xs += 1         # an input pin driven beyond its cell's input-slew index
        r['beyond_table'] = xs
    for r in rows:
        r.setdefault('beyond_table', 0)
    return rows, incomplete, mismatches, nreports, edges


# ---- summaries -----------------------------------------------------------------------------

def q(v, p):
    v = sorted(v)
    if not v:
        return None
    k = (len(v) - 1) * p
    lo = int(k)
    hi = min(lo + 1, len(v) - 1)
    return round(v[lo] + (v[hi] - v[lo]) * (k - lo), 4)


def dist(v):
    return {'n': len(v), 'min': q(v, 0), 'median': q(v, .5), 'p90': q(v, .9), 'max': q(v, 1)} \
        if v else {'n': 0}


SINGLE = ('bench', 'research/base')


def bgroup(b):
    return b if b in SINGLE else 'research/seeded'


def counts(rs):
    out = {'jobs': len(rs), 'any': sum(r['viol_total'] > 0 for r in rs)}
    for c in CHECKS:
        out[c] = sum(r[c + '_pins'] > 0 for r in rs)
    out['on_worst_path'] = sum(r['on_worst_path'] > 0 for r in rs)
    out['slew_ratio'] = dist([r['slew_worst_ratio'] for r in rs if r['slew_pins']])
    out['cap_ratio'] = dist([r['cap_worst_ratio'] for r in rs if r['cap_pins']])
    out['pins'] = dist([r['viol_total'] for r in rs if r['viol_total']])
    return out


def by(rows, keyf):
    g = collections.defaultdict(list)
    for r in rows:
        g[keyf(r)].append(r)
    return g


def job_summary(rs):
    """Short description of the violations of a list of job-stage rows."""
    v = [r for r in rs if r['viol_total']]
    if not v:
        return {'jobs': len(rs), 'with_violation': 0}
    return {'jobs': len(rs), 'with_violation': len(v),
            'on_worst_path': sum(r['on_worst_path'] > 0 for r in v),
            'max_slew_ratio': max((r['slew_worst_ratio'] or 0) for r in v) or None,
            'max_cap_ratio': max((r['cap_worst_ratio'] or 0) for r in v) or None,
            'max_pins': max(r['viol_total'] for r in v),
            'jobs_list': ['%s %s %s %s %s: %s' % (r['build'], r['design'], r['platform'],
                                                   r['flow'], r['stage'], describe(r)) for r in v]}


def describe(r):
    s = []
    for c, u in (('slew', 'ns'), ('cap', r['cap_unit']), ('fanout', '')):
        if r[c + '_pins']:
            s.append('%s %d pins/%d nets, worst %.2f vs limit %.2f %s (x%.2f)%s'
                     % (c, r[c + '_pins'], r[c + '_nets'], r[c + '_worst_value'],
                        r[c + '_worst_limit'], u, r[c + '_worst_ratio'] or 0,
                        ', %d on worst path' % r[c + '_on_worst_path']
                        if r[c + '_on_worst_path'] else ''))
    return '; '.join(s)


def inversions(trow):
    """Delay inversions beyond noise with analyze.py's own definitions (load, noise,
    inversion_shares, on the rows its main() uses: no duplicates, no screen picks): for all rows,
    then without the rows (jobs) that have a route-stage violation, then without those that have
    one on the worst path.  Leaving out a job's row leaves out exactly the pairs that involve it."""
    rows, seeds = AN.load()
    rows = [r for r in rows if not r.get('dup_of') and not r['part'].startswith('screen')]
    _, thr, _ = AN.noise(rows, seeds)
    full = AN.inversion_shares(rows, thr)
    clean = AN.inversion_shares([r for r in rows if not trow(r)['viol_total']], thr)
    offpath = AN.inversion_shares([r for r in rows if not trow(r)['on_worst_path']], thr)
    out = {}
    for k in sorted(full):
        subset, p, f, m = k.split('|')
        if m != 'delay':
            continue
        a, c, o = full[k], clean.get(k, {}), offpath.get(k, {})
        out['%s|%s|%s' % (subset, p, f)] = {
            'beyond_noise_pairs': a['beyond_noise_pairs'], 'inverted': a['inverted'],
            'share': a['share'],
            'pairs_with_violation': a['beyond_noise_pairs'] - c.get('beyond_noise_pairs', 0),
            'inverted_with_violation': a['inverted'] - c.get('inverted', 0),
            'inverted_with_violation_on_path': a['inverted'] - o.get('inverted', 0),
            'share_clean_only': c.get('share'),
            'share_without_on_path': o.get('share')}
    return out


def read_table():
    with open(RES / 'table.csv') as f:
        return list(csv.DictReader(f))


def main():
    M.require()                  # every manifest job present and current, or exit status 1
    rows, incomplete, mismatches, nreports, edges = collect()
    cols = list(rows[0].keys())
    RES.mkdir(exist_ok=True)
    with open(RES / 'electrical.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, cols, lineterminator='\n')
        w.writeheader()
        w.writerows(r for r in rows if r['viol_total'])     # only the violating reports

    J = {'validation': {
        'jobs': len(rows) // 3, 'job_stage_rows': len(rows), 'reports_parsed': nreports,
        'reports_with_violations': sum(r['viol_total'] > 0 for r in rows),
        'violating_pins_total': sum(r['viol_total'] for r in rows),
        'mismatches_vs_metrics': mismatches,
        'incomplete_jobs_without_metrics': incomplete,
        'jobs_by_build': {b: n // 3 for b, n in sorted(collections.Counter(
            r['build'] for r in rows).items())},
        'manifest_jobs_without_metrics': len(incomplete),
        'unfinished_folders_with_reports': sum(bool(x['reports']) for x in incomplete),
        'routing_drc_nonzero': sum(1 for r in rows if r['stage'] == 'route' and r['route_drc']),
        'route_drc_rpt_nonempty': sum(1 for r in rows if r['stage'] == 'route'
                                      and r['route_drc_rpt_bytes']),
        'fanout_limit': 'none: neither Liberty file has max_fanout or default_max_fanout and the '
                        'SDC sets none, so the max fanout check cannot fail',
        'precision': 'report_check_types prints limit, value and slack to 0.01 in library units '
                     '(ns; fF on Nangate45, pF on SKY130HD): a SKY130 cap slack of -0.00 pF is '
                     'an excess below 5 fF'}}

    # by build group, platform, flow, stage
    J['by_build'] = {'%s|%s|%s|%s' % k: counts(v) for k, v in sorted(by(
        rows, lambda r: (bgroup(r['build']), r['platform'], r['flow'], r['stage'])).items())}
    J['by_variant_route'] = {'%s|%s|%s' % k: counts(v) for k, v in sorted(by(
        [r for r in rows if r['stage'] == 'route'],
        lambda r: (r['build'], r['platform'], r['flow'])).items())}
    single = [r for r in rows if r['build'] in ('bench', 'research/base')]
    J['by_size'] = {'%s|%s|%s|%s' % k: counts(v) for k, v in sorted(by(
        single, lambda r: (r['size'], r['platform'], r['flow'], r['stage'])).items())}
    J['by_function_route'] = {'%s|%s|%s' % k: counts(v) for k, v in sorted(by(
        [r for r in single if r['stage'] == 'route'],
        lambda r: (r['function'], r['platform'], r['flow'])).items())}
    viol_route = [r for r in rows if r['stage'] == 'route' and r['viol_total']]
    J['beyond_table_route'] = {
        '%s|%s' % k: {'violating_jobs': len(v), 'with_pin_beyond_table': sum(r['beyond_table'] > 0
                                                                             for r in v)}
        for k, v in sorted(by(viol_route, lambda r: (r['platform'], r['flow'])).items())}
    J['limits_vs_tables'] = {p: {c: e for c, e in sorted(edges[p].items())} for p in PLATS}

    idx = {(r['build'], r['design'], r['platform'], r['flow'], r['stage']): r for r in rows}
    builds_of = collections.defaultdict(set)
    for r in rows:
        builds_of[r['design']].add(r['build'])

    def jobs_of(design, plats=PLATS, flows=FLOWS, stages=STAGES, builds=None):
        return [idx[(b, design, p, f, s)] for b in sorted(builds_of[design])
                if builds is None or b in builds
                for p in plats for f in flows for s in stages if (b, design, p, f, s) in idx]

    claims = {}
    # (a) first pair and the 59 pairs of the benchmark
    fp = ('ours--aes-invsbox-a40-ad4-g134-gd12-xx94-41', 'nist--aes-invsbox-a45-ad4-g141-gd12-xx96-25')
    claims['a_first_pair'] = {
        d: {st: job_summary(jobs_of(d, stages=(st,))) for st in STAGES} for d in fp}
    bench = [r for r in rows if r['build'] == 'bench' and r['stage'] == 'route']
    meta = {}
    for r in bench:
        meta.setdefault(r['design'], type('D', (), {
            'id': r['design'], 'origin': r['origin'], 'function': r['function'],
            'metrics': {k: r[k] for k in ('A', 'AD', 'G', 'GD')}}))
    designs = list(meta.values())
    prs = [(n, o) for n, o in PR.pair([d for d in designs if d.origin == 'ours'],
                                      [d for d in designs if d.origin == 'nist']) if o]
    comp = []
    for n, o in prs:
        for p in PLATS:
            for f in FLOWS:
                e = {'nist': n.id, 'ours': o.id, 'platform': p, 'flow': f}
                for st in STAGES:
                    a, b = idx[('bench', o.id, p, f, st)], idx[('bench', n.id, p, f, st)]
                    e[st + '_viol'] = [x for x, r in (('ours', a), ('nist', b)) if r['viol_total']]
                    e[st + '_on_path'] = [x for x, r in (('ours', a), ('nist', b))
                                          if r['on_worst_path']]
                ro, rn = idx[('bench', o.id, p, f, 'route')], idx[('bench', n.id, p, f, 'route')]
                e['delay_change'] = round(ro['delay_ns'] / rn['delay_ns'] - 1, 4)
                e['ours_faster'] = ro['delay_ns'] < rn['delay_ns']
                e['detail'] = {x: describe(r) for x, r in (('ours', ro), ('nist', rn))
                               if r['viol_total']}
                comp.append(e)
    pcount = {}
    for p in PLATS:
        for f in FLOWS:
            cs = [c for c in comp if c['platform'] == p and c['flow'] == f]
            clean = [c for c in cs if not c['route_viol']]
            pcount['%s|%s' % (p, f)] = {
                'pairs': len(cs), 'route_viol': len(cs) - len(clean),
                'route_on_path': sum(bool(c['route_on_path']) for c in cs),
                'synth_viol': sum(bool(c['synth_viol']) for c in cs),
                'place_viol': sum(bool(c['place_viol']) for c in cs),
                'ours_faster_all': sum(c['ours_faster'] for c in cs),
                'ours_faster_clean': sum(c['ours_faster'] for c in clean), 'clean': len(clean)}
    claims['a_pairs'] = {
        'pairs': len(prs), 'comparisons': len(comp),
        'comparisons_route_viol': sum(bool(c['route_viol']) for c in comp),
        'comparisons_route_on_path': sum(bool(c['route_on_path']) for c in comp),
        'comparisons_any_stage_viol': sum(bool(c['route_viol'] or c['place_viol'] or c['synth_viol'])
                                          for c in comp),
        'pairs_with_any_route_viol': len({(c['nist'], c['ours']) for c in comp if c['route_viol']}),
        'per_config': pcount,
        'affected': [c for c in comp if c['route_viol'] or c['place_viol'] or c['synth_viol']]}

    # (b) exact comparisons of the README
    exact = [('aes-sbox-a57-ad9-g152-gd36-hb2092f6d0c4adc01', 'aes-sbox-a30-ad4-g147-gd36-xx117-13', 'ADP'),
             ('aes-sbox-a68-ad13-g176-gd37-hdd064a2dd98cf1eb', 'aes-sbox-a28-ad5-g172-gd27-hb9d61cfc26a4a3bb', 'area'),
             ('aes-invsbox-a31-ad5-g138-gd20-h18e16082a70397f', 'aes-invsbox-a28-ad4-g135-gd20-xx107-35', 'ADP'),
             ('aes-invsbox-a54-ad4-g144-gd16-h2d9970ea050c359', 'aes-invsbox-a28-ad4-g143-gd16-xxn115-59-1', 'power'),
             ('aes-mixcolumns-xor117-depth6-hac7ce23fbc1f9bb9', 'aes-mixcolumns-xor95-depth6-hfca2934f2afadbfa', 'delay'),
             ('aes-invmixcolumns-xor351-depth7-h7711bf97e4bcf', 'aes-invmixcolumns-xor113-depth7-h5e49d90bd57a4', 'delay'),
             ('aes-sbox-sel-a36-ad6-g241-gd26-hcb958a27654d38', 'aes-sbox-sel-a36-ad6-g191-gd26-xx155-31', 'delay')]
    alld = sorted(builds_of)

    def find(name):
        m = [d for d in alld if d.split('--', 1)[1].startswith(name)]
        if len(m) != 1:
            raise SystemExit('circuit %s: %d matches %s' % (name, len(m), m))
        return m[0]
    claims['b_exact'] = []
    for worse, better, meas in exact:
        dw, db = find(worse), find(better)
        claims['b_exact'].append({'worse': dw, 'beats': db, 'measure': meas, **{
            st: {'worse': job_summary(jobs_of(dw, stages=(st,))),
                 'beats': job_summary(jobs_of(db, stages=(st,)))} for st in STAGES}})

    # same-metric groups (analyze.py's: non-screen, non-duplicate rows of an iso key, n >= 4)
    table = read_table()
    tb = [t for t in table if not t['part'].startswith('screen') and not t.get('dup_of')]
    iso_keys = {(t['function'], t['key']) for t in tb if t['part'] == 'iso'}
    groups = by([t for t in tb if (t['function'], t['key']) in iso_keys],
                lambda t: (t['function'], t['key'], t['platform'], t['flow']))
    groups = {k: v for k, v in groups.items() if len(v) >= 4}

    def trow(t, st='route'):
        b = 'bench' if t['part'] == 'baseline' else 'research/base'
        return idx[(b, t['circuit'], t['platform'], t['flow'], st)]

    repeats = sorted({r['build'] for r in rows} - set(SINGLE))

    def group_check(k, v):
        ranked = sorted(v, key=lambda t: float(t['delay']))
        mem = []
        for rank, t in enumerate(ranked, 1):
            r = trow(t)
            seeded = [idx[(b, t['circuit'], t['platform'], t['flow'], 'route')]
                      for b in repeats if (b, t['circuit'], t['platform'], t['flow'], 'route') in idx]
            mem.append({'circuit': t['circuit'], 'part': t['part'], 'rank_delay': rank,
                        'delay': float(t['delay']), 'route_viol': describe(r) if r['viol_total'] else '',
                        'on_worst_path': r['on_worst_path'],
                        'seeded_runs': len(seeded),
                        'seeded_with_viol': sum(s['viol_total'] > 0 for s in seeded),
                        'synth_viol': trow(t, 'synth')['viol_total'],
                        'place_viol': trow(t, 'place')['viol_total']})
        return mem
    claims['c_published'] = {}
    for fn, key in (('aes-mixcolumns', '0/0/88/5'), ('aes-sbox', '32/4/114/19')):
        for p in PLATS:
            for f in ('preserve', 'free-area'):
                claims['c_published']['%s %s|%s|%s' % (fn, key, p, f)] = group_check(
                    (fn, key, p, f), groups[(fn, key, p, f)])

    # (d) the prospective screen, preserve flow
    scr = [t for t in table if t['part'].startswith('screen') and t['flow'] == 'preserve']
    sc = {}
    for k, v in sorted(by(scr, lambda t: (t['function'] + ' ' + t['key'], t['platform'],
                                          t['part'])).items()):
        rs = [trow(t) for t in v]
        sc['%s|%s|%s' % k] = {'jobs': len(rs), 'route_viol': sum(r['viol_total'] > 0 for r in rs),
                              'on_worst_path': sum(r['on_worst_path'] > 0 for r in rs),
                              'synth_viol': sum(trow(t, 'synth')['viol_total'] > 0 for t in v),
                              'place_viol': sum(trow(t, 'place')['viol_total'] > 0 for t in v),
                              'max_ratio': max([r['slew_worst_ratio'] or 0 for r in rs] +
                                               [r['cap_worst_ratio'] or 0 for r in rs]) or None}
    allscr = [t for t in table if t['part'].startswith('screen')]
    claims['d_screen_preserve'] = sc
    claims['d_screen_all_flows'] = {
        '%s|%s' % k: {'jobs': len(v), 'route_viol': sum(trow(t)['viol_total'] > 0 for t in v)}
        for k, v in sorted(by(allscr, lambda t: (t['platform'], t['flow'])).items())}

    # (e) same-metric groups generally
    ge = {}
    for (fn, key, p, f), v in sorted(groups.items()):
        mem = group_check((fn, key, p, f), v)
        ge['%s %s|%s|%s' % (fn, key, p, f)] = {
            'n': len(mem), 'members_viol': sum(bool(m['route_viol']) for m in mem),
            'members_on_path': sum(m['on_worst_path'] > 0 for m in mem),
            'best_viol': bool(mem[0]['route_viol']), 'worst_viol': bool(mem[-1]['route_viol']),
            'best_on_path': mem[0]['on_worst_path'] > 0, 'worst_on_path': mem[-1]['on_worst_path'] > 0,
            'rel_range': round((mem[-1]['delay'] - mem[0]['delay']) /
                               statistics.median(m['delay'] for m in mem), 4),
            'rel_range_clean': (lambda c: round((c[-1]['delay'] - c[0]['delay']) /
                                                statistics.median(m['delay'] for m in c), 4)
                                if len(c) >= 2 else None)([m for m in mem if not m['route_viol']]),
            'violating': [m['circuit'] + ' (rank %d)' % m['rank_delay'] for m in mem
                          if m['route_viol']]}
    claims['e_groups'] = ge

    # (f) dominance inversions of routed delay (analyze.py's inversion_shares), with and without
    # the pairs in which either job has a route-stage violation
    claims['f_inversions'] = inversions(trow)
    J['claims'] = claims
    with open(RES / 'electrical.json', 'w') as f:
        json.dump(J, f, indent=1, sort_keys=True)
        f.write('\n')
    write_md(J, rows)
    print('wrote', RES / 'electrical.csv', sum(r['viol_total'] > 0 for r in rows), 'rows;', RES / 'electrical.json;',
          RES / 'ELECTRICAL.md')
    print('reports parsed', nreports, 'mismatches', len(mismatches), 'incomplete', len(incomplete))


# ---- Markdown ------------------------------------------------------------------------------

def pct(a, b):
    return '%d (%.0f%%)' % (a, 100.0 * a / b) if b else '0'


def fr(d):
    return '–' if not d or not d.get('n') else '%.2f / %.2f' % (d['median'], d['max'])


def pc(x):
    return '–' if x is None else '%.1f%%' % (100 * x)


def claims_summary(J):
    """The generated verdicts on the highlighted comparisons (section 'Claims check')."""
    C = J['claims']
    md = ['## Claims check', '',
          'Whether the jobs that the highlighted comparisons rely on have electrical violations '
          '(route stage unless stated; details in the sections below).', '']
    fp = C['a_first_pair']
    n = sum(s['with_violation'] for d in fp.values() for s in d.values())
    md.append('- **(a) First pair** (BoolFlux 40/4/134/12 vs NIST 45/4/141/12): %s at any stage '
              'in %s jobs per circuit (benchmark and every repeat).'
              % ('no violation' if not n else '%d job-stages with violations' % n,
                 ' / '.join(str(d['route']['jobs']) for d in fp.values())))
    a = C['a_pairs']
    pcs = a['per_config']
    md.append('- **(a) The %d benchmark pairs** (%d comparisons): %d involve a job with a route-stage '
              'violation, %d of them on a worst path (%d at any stage). Ours faster, all pairs / '
              'without the violating comparisons: %s.'
              % (a['pairs'], a['comparisons'], a['comparisons_route_viol'],
                 a['comparisons_route_on_path'], a['comparisons_any_stage_viol'],
                 '; '.join('%s %s %d/%d / %d/%d' % (tuple(k.split('|')) + (
                     c['ours_faster_all'], c['pairs'], c['ours_faster_clean'], c['clean']))
                     for k, c in pcs.items())))
    bad = [e for e in C['b_exact'] if any(e[st][s]['with_violation'] for st in STAGES
                                          for s in ('worse', 'beats'))]
    txt = []
    for e in bad:
        for side in ('worse', 'beats'):
            r = e['route'][side]
            if r['with_violation']:
                worst = ', '.join('worst %s x%.2f' % (c, r[k]) for c, k in
                                  (('cap', 'max_cap_ratio'), ('slew', 'max_slew_ratio')) if r[k])
                txt.append('`%s` (%s claim): %d of %d route jobs, %d on the worst path, %s'
                           % (e[side].split('--')[1], e['measure'], r['with_violation'],
                              r['jobs'], r['on_worst_path'], worst))
    md.append('- **(b) Exact comparisons**: %d of %d rows clean in every job and stage of both '
              'circuits%s.' % (len(C['b_exact']) - len(bad), len(C['b_exact']),
                               ('; ' + '; '.join(txt)) if txt else ''))
    cv = {k: sum(bool(m['route_viol']) or m['seeded_with_viol'] > 0 or m['synth_viol'] > 0
                 or m['place_viol'] > 0 for m in mem) for k, mem in C['c_published'].items()}
    md.append('- **(c) Published circuits in their own class** (MixColumns 88@5, S-box '
              '32/4/114/19; preserve and free-area, both libraries): %d members with a violation '
              'at any stage or in any repeat, over %d group cells.' % (sum(cv.values()), len(cv)))
    d = C['d_screen_all_flows']
    md.append('- **(d) Prospective screen**: %d of %d screen jobs with a route-stage violation '
              '(all flows; preserve: %d at synth or place).'
              % (sum(c['route_viol'] for c in d.values()), sum(c['jobs'] for c in d.values()),
                 sum(c['synth_viol'] + c['place_viol'] for c in C['d_screen_preserve'].values())))
    ge = C['e_groups']
    moved = sorted(((abs(g['rel_range'] - g['rel_range_clean']), k, g) for k, g in ge.items()
                    if g['members_viol'] and g['rel_range_clean'] is not None), reverse=True)
    md.append('- **(e) Same-metric groups**: %d of %d group x library x flow cells have a violating '
              'member; the fastest member violates in %d, the slowest in %d; the largest changes '
              'of a group\'s delay range without its violating members: %s.'
              % (sum(g['members_viol'] > 0 for g in ge.values()), len(ge),
                 sum(g['best_viol'] for g in ge.values()), sum(g['worst_viol'] for g in ge.values()),
                 '; '.join('%s %.1f%% to %.1f%%' % (k.replace('|', ' '), 100 * g['rel_range'],
                                                    100 * g['rel_range_clean'])
                           for _, k, g in moved[:2]) or 'none'))
    f = C['f_inversions']
    md.append('- **(f) Delay inversions** (analyze.py\'s inversion_shares): G < 400 share with / '
              'without violating jobs: %s. All circuits (with the G >= 400 ones): %s.'
              % ('; '.join('%s %s %s / %s' % (tuple(k.split('|')[1:]) + (pc(v['share']),
                                                                      pc(v['share_clean_only'])))
                           for k, v in f.items() if k.startswith('G<400')),
                 '; '.join('%s %s %s / %s' % (tuple(k.split('|')[1:]) + (pc(v['share']),
                                                                      pc(v['share_clean_only'])))
                           for k, v in f.items() if k.startswith('all'))))
    return md + ['']


def write_md(J, rows):
    V, C = J['validation'], J['claims']
    md = ['# Electrical checks: max slew, max capacitance, max fanout', '',
          'Generated by `python3 hardware/research/electrical.py` from OpenSTA\'s '
          '`report_check_types -max_slew -max_capacitance -max_fanout -violators`, which '
          'hwbench/flow.py writes after synthesis, placement and routing of every job. These are '
          'electrical design-rule checks of STA against the Liberty limits (pin transition, net '
          'load, fanout). They are **not routing DRC**: detailed routing\'s design-rule count is '
          '0 for every reported job (%d of %d routed jobs non-zero; route_drc.rpt empty in all '
          'but %d). The flow runs no buffering, sizing or repair, so a violation is what synthesis, '
          'or the circuit itself in the preserve flow, produced. Jobs are the study\'s manifest '
          '(manifest.py: the benchmark\'s jobs and every research variant\'s), every one of them '
          'counted below, including those without any violation. '
          '[electrical.csv](electrical.csv) lists **only the job-stage reports with at least one '
          'violation** (%d rows); all counts and distributions: [electrical.json](electrical.json).'
          % (V['routing_drc_nonzero'], V['jobs'], V['route_drc_rpt_nonempty'],
             V['reports_with_violations']), '']
    md += claims_summary(J)
    md += ['## Validation', '',
          '- %d jobs (%s), %d reports parsed by a strict parser (any unrecognised line is an '
          'error); %d of the %d job-stage reports have violations, %d violating pins in all.'
          % (V['jobs'], ', '.join('%s %d' % kv for kv in V['jobs_by_build'].items()),
             V['reports_parsed'], V['reports_with_violations'], V['job_stage_rows'],
             V['violating_pins_total']),
          '- Parsed rows against metrics.json `drv_violations` (flow.py counts "VIOLATED"): '
          '**%d mismatches**.' % len(V['mismatches_vs_metrics']),
          '- %d jobs of the manifest have no metrics.json (not finished; in no table), %d of '
          'them with a folder holding some reports: left out of every count here (their reports '
          'parse too). Folders outside the manifest (build/_revalidate, build/timing, superseded '
          'runs) are never read.'
          % (V['manifest_jobs_without_metrics'], V['unfinished_folders_with_reports']),
          '- Max fanout: %s.' % V['fanout_limit'],
          '- Precision: %s.' % V['precision'], '',
          '## Jobs with a violation', '',
          'Per build, library, flow and stage: jobs with any violation, with a max-slew and with a '
          'max-capacitance violation, and with a violating pin or net on the reported worst '
          '(critical) path. Ratio: worst violating value / its limit, median / max over the '
          'violating jobs. Builds: the benchmark (`bench`), the study\'s base run, and its 5 '
          'seeded repeats pooled.', '',
          '| Build | Library | Flow | Stage | Jobs | Any | Slew | Cap | On worst path | Slew ratio | Cap ratio |',
          '|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for k, c in J['by_build'].items():
        b, p, f, st = k.split('|')
        md.append('| %s | %s | %s | %s | %d | %s | %d | %d | %d | %s | %s |'
                  % (b, p, f, st, c['jobs'], pct(c['any'], c['jobs']), c['slew'], c['cap'],
                     c['on_worst_path'], fr(c['slew_ratio']), fr(c['cap_ratio'])))
    md += ['', 'No job has a max-fanout violation (no limit is defined).', '',
           '### By circuit size (benchmark and base run, single runs)', '',
           '| Size | Library | Flow | Stage | Jobs | Any | Slew | Cap | On worst path | Slew ratio | Cap ratio |',
           '|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for k, c in J['by_size'].items():
        s, p, f, st = k.split('|')
        if st != 'route':
            continue
        md.append('| %s | %s | %s | %s | %d | %s | %d | %d | %d | %s | %s |'
                  % (s, p, f, st, c['jobs'], pct(c['any'], c['jobs']), c['slew'], c['cap'],
                     c['on_worst_path'], fr(c['slew_ratio']), fr(c['cap_ratio'])))
    md += ['', '### Beyond the Liberty tables (route stage)', '',
           'A violation outside the range of the cell\'s delay/transition tables means STA '
           'extrapolated. In both libraries each output pin\'s max_capacitance is the last load '
           'index of its tables and the input-slew index ends at the transition limit (Nangate45 '
           '0.1985 ns, its default_max_transition; SKY130HD 1.5 ns), so a violation means '
           'extrapolated delay, slew and internal power for the cells concerned (a few count as '
           'not beyond only because the printed value rounds to the limit). Cells and limits: '
           '`limits_vs_tables` in electrical.json.', '',
           '| Library | Flow | Violating jobs | With a pin beyond the tables |', '|---|---|---:|---:|']
    for k, c in J['beyond_table_route'].items():
        p, f = k.split('|')
        md.append('| %s | %s | %d | %d |' % (p, f, c['violating_jobs'], c['with_pin_beyond_table']))

    # claims
    md += ['', '## The highlighted comparisons', '']
    a = C['a_pairs']
    md += ['### (a) The benchmark\'s pairs', '',
           'First pair, BoolFlux 40/4/134/12 against NIST 45/4/141/12, every build and variant:', '']
    for d, sts in C['a_first_pair'].items():
        md.append('- `%s`: %s' % (d, '; '.join(
            '%s %d of %d jobs' % (st, s['with_violation'], s['jobs']) for st, s in sts.items())))
        for st, s in sts.items():
            for j in s.get('jobs_list', []):
                md.append('  - %s' % j)
    md += ['', '%d pairs x 6 configurations = %d comparisons. With a violation in either job: '
           '%d at the route stage (%d with a violating pin on a worst path), %d at any stage; '
           '%d of the %d pairs have one in some configuration at the route stage.'
           % (a['pairs'], a['comparisons'], a['comparisons_route_viol'],
              a['comparisons_route_on_path'], a['comparisons_any_stage_viol'],
              a['pairs_with_any_route_viol'], a['pairs']), '',
           '| Library | Flow | Pairs | Route viol. | On worst path | Synth viol. | Place viol. | '
           'Ours faster (all) | Ours faster (clean pairs only) |',
           '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for k, c in a['per_config'].items():
        p, f = k.split('|')
        md.append('| %s | %s | %d | %d | %d | %d | %d | %d/%d | %d/%d |'
                  % (p, f, c['pairs'], c['route_viol'], c['route_on_path'], c['synth_viol'],
                     c['place_viol'], c['ours_faster_all'], c['pairs'], c['ours_faster_clean'],
                     c['clean']))
    md += ['', 'Comparisons with a violation (route-stage detail; delay change of ours vs NIST, '
           'routed):', '']
    for c in a['affected']:
        md.append('- %s vs %s, %s %s: route %s, place %s, synth %s; delay %+.1f%%. %s'
                  % (c['ours'].split('--')[1], c['nist'].split('--')[1], c['platform'], c['flow'],
                     '/'.join(c['route_viol']) or '-', '/'.join(c['place_viol']) or '-',
                     '/'.join(c['synth_viol']) or '-', 100 * c['delay_change'],
                     ' | '.join('%s: %s' % kv for kv in c['detail'].items())))
    md += ['', '### (b) Exact comparisons (README), every build and variant', '',
           '| Worse circuit | Beats | Measure | Route jobs with viol. (worse / beats) | '
           'On worst path | Synth | Place |', '|---|---|---|---|---|---|---|']
    for e in C['b_exact']:
        r = e['route']

        def wb(s, key='with_violation'):
            return '%s / %s' % ('%d of %d' % (s['worse'][key] if key in s['worse'] else 0,
                                              s['worse']['jobs']),
                                '%d of %d' % (s['beats'][key] if key in s['beats'] else 0,
                                              s['beats']['jobs']))
        md.append('| `%s` | `%s` | %s | %s | %s | %s | %s |'
                  % (e['worse'].split('--')[1], e['beats'].split('--')[1], e['measure'], wb(r),
                     wb(r, 'on_worst_path'), wb(e['synth']), wb(e['place'])))
    for e in C['b_exact']:
        for st in STAGES:
            for side in ('worse', 'beats'):
                for j in e[st][side].get('jobs_list', []):
                    md.append('- %s' % j)
    md += ['', '### (c) Published circuits in their own metric class (route, base runs)', '',
           'Members ranked by routed delay (table.csv, single base run); violations of the base run '
           'and how many of the seeded repeats have one.', '']
    for k, mem in C['c_published'].items():
        nv = sum(bool(m['route_viol']) or m['seeded_with_viol'] > 0 or m['synth_viol'] > 0
                 or m['place_viol'] > 0 for m in mem)
        md.append('- **%s** (%d members, %d with a violation at any stage or in any seeded '
                  'repeat): %s' % (k, len(mem), nv, '; '.join(
            '%d %s%s%s' % (m['rank_delay'], m['circuit'].split('--')[0],
                           (' [viol: %s]' % m['route_viol']) if m['route_viol'] else '',
                           (' [seeded %d/%d viol]' % (m['seeded_with_viol'], m['seeded_runs']))
                           if m['seeded_with_viol'] else '')
            for m in mem)))
    md += ['', '### (d) Prospective screen, preserve flow (route)', '',
           '| Pool | Library | Pick | Jobs | Route viol. | On worst path | Synth | Place | Max ratio |',
           '|---|---|---|---:|---:|---:|---:|---:|---:|']
    for k, c in C['d_screen_preserve'].items():
        pool, p, part = k.split('|')
        md.append('| %s | %s | %s | %d | %d | %d | %d | %d | %s |'
                  % (pool, p, part[7:], c['jobs'], c['route_viol'], c['on_worst_path'],
                     c['synth_viol'], c['place_viol'],
                     '%.2f' % c['max_ratio'] if c['max_ratio'] else '–'))
    md += ['', 'All flows: ' + '; '.join('%s %d of %d' % (k.replace('|', ' '), c['route_viol'],
                                                           c['jobs'])
                                         for k, c in C['d_screen_all_flows'].items()) + '.']
    ge = C['e_groups']
    md += ['', '### (e) Same-metric groups (route, base runs)', '',
           '%d group x library x flow cells (n >= 4). With any violating member: %d; best (fastest) '
           'member violating: %d (on its worst path: %d); slowest member violating: %d (on its '
           'worst path: %d).'
           % (len(ge), sum(g['members_viol'] > 0 for g in ge.values()),
              sum(g['best_viol'] for g in ge.values()), sum(g['best_on_path'] for g in ge.values()),
              sum(g['worst_viol'] for g in ge.values()), sum(g['worst_on_path'] for g in ge.values())),
           '', '| Group | Library | Flow | n | Violating | Range | Range without them | Violating members |',
           '|---|---|---|---:|---:|---:|---:|---|']
    for k, g in ge.items():
        if not g['members_viol']:
            continue
        grp, p, f = k.split('|')
        md.append('| %s | %s | %s | %d | %d | %.1f%% | %s | %s |'
                  % (grp, p, f, g['n'], g['members_viol'], 100 * g['rel_range'],
                     '%.1f%%' % (100 * g['rel_range_clean']) if g['rel_range_clean'] is not None
                     else '–', ', '.join('`%s`' % v for v in g['violating'])))
    md += ['', '### (f) Dominance inversions of routed delay (base runs)', '',
           'Pairs where one circuit dominates the other in (A, AD, G, GD) and the routed delays '
           'differ beyond noise (analyze.py\'s rule; "share" is the share where the logically '
           'worse circuit is faster). Recomputed here, then without the pairs in which either job '
           'has a route-stage violation. The "all" subset includes the 41 circuits with G >= 400, '
           'which carry most violations (and most violations on a worst path); removing their '
           'pairs also removes most large-circuit pairs, so "share without them" is not the share '
           'with the violations repaired.', '',
           '| Subset | Library | Flow | Pairs beyond noise | Share inverted | Inverted pairs with a '
           'violating job | of them on a worst path | Share without violating jobs | Share without '
           'worst-path violations |',
           '|---|---|---|---:|---:|---:|---:|---:|---:|']
    for k, a in C['f_inversions'].items():
        s, p, f = k.split('|')
        md.append('| %s | %s | %s | %d | %s | %d of %d | %d | %s | %s |'
                  % (s, p, f, a['beyond_noise_pairs'], pc(a['share']),
                     a['inverted_with_violation'], a['inverted'],
                     a['inverted_with_violation_on_path'], pc(a['share_clean_only']),
                     pc(a['share_without_on_path'])))
    (RES / 'ELECTRICAL.md').write_text('\n'.join(md) + '\n')


if __name__ == '__main__':
    main()
