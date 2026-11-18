#!/usr/bin/env python3
"""Statistics on the repeated runs (results/table.csv base values + results/seeds.csv) -> results/seeded.json, SEEDED.md

    python3 hardware/research/seeded.py

Every run is a cell (O, P) of a statement-order x placement-setting grid for one (circuit, library,
flow):

    base      O = 0, P = 0  (the benchmark itself)
    pnr<K>    O = 0, P = K  (RePlAce's global-placement parameters perturbed by seed K)
    synth<K>  O = K, P = K  (RTL statements in seeded order K, and placement setting K)
    o<O>p<P>  O, P

Free flows (free, free-area): Yosys + ABC see the statement order, so the runs are placements
nested in orders.  The unit of every free-flow test is the ORDER MEAN (the mean of that order's
placements), orders weighted equally; the summary of a circuit is the mean of its order means.
Placement variance is the pooled within-order variance; order variance is estimated by moments:
    E[var(order means)] = s2_order + s2_place * mean(1 / n_o)
so s2_order = var(order means) - s2_place * mean(1 / n_o) (negative -> 0 in shares; the raw value
is kept).  With the current runs n_o = (4, 1, 1) for orders 0, 1, 2.  When the runs contain a
balanced core (>= 3 orders sharing >= 2 placement settings), the free-flow analysis uses that core
only (two-level nested ANOVA: orders, placements within orders) and adds a crossed check of a
placement setting effect common to all orders.

Preserve flow: the netlist is one cell per gate whatever the order, so the runs are placements of
one netlist; the unit is the RUN (one per placement setting P; repeats of the same P under another
O are the same job and kept once).

The old analysis (every run of a free flow pooled as an independent observation, which weights
order 0 4:1:1) is kept as a labelled sensitivity line everywhere.

  noise        per library, flow, measure: median placement CV, order CV, single-run CV
  groups       same-metric groups: one-way ANOVA between circuits (unit as above), F-test p, ICC(1),
               and the variance components circuit / order / placement
  inversions   the repeated apparent dominance inversions: per configuration the gain of the
               logically worse circuit, one-sided Welch t-test and exact permutation test
               (worse < better) on the units above, Holm-corrected over the whole table
  first pair   the benchmark's first pair, means and standard deviations under the hierarchy

Everything here is exploratory: 3 order means per circuit give Welch tests with 2-4 degrees of
freedom, and an exact permutation test of 3 against 3 cannot go below p = 1/20 = 0.05.
"""
from __future__ import annotations

import collections
import csv
import itertools
import json
import os
import pathlib
import re
import warnings

import numpy as np
from scipy import stats

HERE = pathlib.Path(__file__).resolve().parent
RES = pathlib.Path(os.environ.get('HWRESEARCH_RESULTS', HERE / 'results'))   # results/, or a staging folder
MEAS = ('area', 'delay', 'adp', 'power')
CONFIGS = [(p, f) for p in ('nangate45', 'sky130hd') for f in ('preserve', 'free', 'free-area')]
ALPHA = 0.05
FIRST_PAIR = ('ours--aes-invsbox-a40-ad4-g134-gd12-xx94-41', 'nist--aes-invsbox-a45-ad4-g141-gd12-xx96-25')
# the README's "Exact comparisons": (logically worse circuit, measure)
EXACT = {('aes-sbox-a57-ad9-g152-gd36-hb2092f6d0c4adc01', 'adp'),
         ('aes-sbox-a68-ad13-g176-gd37-hdd064a2dd98cf1eb', 'area'),
         ('aes-invsbox-a31-ad5-g138-gd20-h18e16082a70397fb', 'adp'),
         ('aes-invsbox-a54-ad4-g144-gd16-h2d9970ea050c3592', 'power'),
         ('aes-mixcolumns-xor117-depth6-hac7ce23fbc1f9bb9', 'delay'),
         ('aes-invmixcolumns-xor351-depth7-h7711bf97e4bcf8b8', 'delay'),
         ('aes-sbox-sel-a36-ad6-g241-gd26-hcb958a27654d3809', 'delay')}
# selection reuse: the pairs were chosen on o0p0, the balanced circuits after pnr1-3 / synth1-2 were
# seen.  Fresh data: (free-flow orders, preserve placements, description); free-flow order means over
# placements FRESH_PL
FRESH_PL = (0, 1, 2)
SCEN = {'fresh': ((3, 4, 5), (4, 5), 'free flows: orders 3-5 (3 order means); preserve: placements 4-5 '
                                     '(2 runs); none of it seen before the balanced set was chosen'),
        'without_selection_order': ((1, 2, 3, 4, 5), (1, 2, 3, 4, 5),
                                    'free flows: orders 1-5 (order 0, the netlist of the selection run o0p0, '
                                    'left out); preserve: placements 1-5 (o0p0 left out)')}


def short(c):
    return c.split('--', 1)[1]


def cell(variant):
    """(order, placement) of a variant name."""
    if variant == 'base':
        return 0, 0
    m = re.fullmatch(r'pnr(\d+)', variant)
    if m:
        return 0, int(m.group(1))
    m = re.fullmatch(r'synth(\d+)', variant)
    if m:
        return int(m.group(1)), int(m.group(1))
    m = re.fullmatch(r'o(\d+)p(\d+)', variant)
    if m:
        return int(m.group(1)), int(m.group(2))
    raise ValueError('variant %s' % variant)


def holm(ps):
    """Step-down Holm adjusted p-values (same order as ps)."""
    k = len(ps)
    out = [None] * k
    running = 0.0
    for rank, i in enumerate(sorted(range(k), key=lambda i: (ps[i], i))):
        running = max(running, min(1.0, (k - rank) * ps[i]))
        out[i] = running
    return out


def perm_p(x, y):
    """Exact one-sided permutation p of mean(x) - mean(y) being this low (all splits enumerated)."""
    z = np.concatenate([x, y])
    obs = x.mean() - y.mean()
    tol = 1e-12 * max(1.0, float(np.abs(z).max()))
    n, hit = 0, 0
    tot = z.sum()
    for idx in itertools.combinations(range(len(z)), len(x)):
        sx = z[list(idx)].sum()
        d = sx / len(x) - (tot - sx) / len(y)
        n += 1
        hit += d <= obs + tol
    return hit / n, 1.0 / n


def welch_p(x, y, gain):
    if np.ptp(np.concatenate([x, y])) == 0 or (np.ptp(x) == 0 and np.ptp(y) == 0):
        return 0.0 if gain > 0 else 1.0
    return float(stats.ttest_ind(x, y, equal_var=False, alternative='less').pvalue)


class Runs:
    """The runs of one (circuit, library, flow) as order -> placement -> measures."""

    def __init__(self, flow):
        self.flow = flow
        self.grid = {}           # (O, P) -> {measure: value}
        self.dups = 0            # repeats of the same job (same cell; same P in preserve)
        self.dup_mismatch = 0

    def add(self, o, p, vals):
        if self.flow == 'preserve':
            o = 0                # one netlist: only the placement setting matters
        if (o, p) in self.grid:
            self.dups += 1
            if any(abs(self.grid[(o, p)][m] - vals[m]) > 1e-9 * max(1.0, abs(vals[m])) for m in MEAS):
                self.dup_mismatch += 1
            return
        self.grid[(o, p)] = vals

    def orders(self):
        out = collections.defaultdict(dict)
        for (o, p), v in sorted(self.grid.items()):
            out[o][p] = v
        return dict(out)

    def balanced_core(self):
        """(orders, placements) of a balanced core: >= 3 orders all having the same >= 2 placements."""
        od = self.orders()
        if self.flow == 'preserve' or len(od) < 3:
            return None
        common = set.intersection(*(set(v) for v in od.values()))
        if len(common) < 2:
            return None
        return sorted(od), sorted(common)

    def nruns(self):
        return len(self.grid)

    def summary(self, m):
        """Hierarchical summary of measure m."""
        od = self.orders()
        allv = np.array([v[m] for _, v in sorted(self.grid.items())])
        old = {'n': len(allv), 'mean': float(allv.mean()),
               'sd': float(allv.std(ddof=1)) if len(allv) > 1 else None}
        if self.flow == 'preserve':
            x = np.array([od[0][p][m] for p in sorted(od[0])])
            sd = float(x.std(ddof=1)) if len(x) > 1 else None
            return {'unit': 'placement run', 'units': x, 'mean': float(x.mean()), 'n_eff': len(x),
                    'sd_unit': sd, 's2_place': sd ** 2 if sd is not None else None, 's2_order': None,
                    'sd_single_run': sd, 'design': {'0': sorted(od[0])}, 'balanced': None, 'old': old}
        core = self.balanced_core()
        if core:
            os_, ps = core
            od = {o: {p: od[o][p] for p in ps} for o in os_}
        means, ss, df, inv_n = [], 0.0, 0, []
        for o in sorted(od):
            v = np.array([od[o][p][m] for p in sorted(od[o])])
            means.append(v.mean())
            ss += ((v - v.mean()) ** 2).sum()
            df += len(v) - 1
            inv_n.append(1.0 / len(v))
        means = np.array(means)
        s2p = ss / df if df else None
        vm = float(means.var(ddof=1)) if len(means) > 1 else None
        s2o = None if vm is None or s2p is None else vm - s2p * float(np.mean(inv_n))
        single = None
        if s2o is not None:
            single = float(np.sqrt(max(s2o, 0.0) + s2p))
        res = {'unit': 'order mean', 'units': means, 'mean': float(means.mean()), 'n_eff': len(means),
               'sd_unit': float(np.sqrt(vm)) if vm is not None else None,
               's2_place': s2p, 'place_df': df, 's2_order': s2o, 'sd_single_run': single,
               'design': {str(o): sorted(od[o]) for o in sorted(od)},
               'balanced': {'orders': core[0], 'placements': core[1]} if core else None, 'old': old}
        if core:
            # two-level nested ANOVA (orders; placements within orders) and a crossed check: is there
            # a placement-setting effect common to all orders?
            os_, ps = core
            Y = np.array([[od[o][p][m] for p in ps] for o in os_])
            O, P = Y.shape
            g = Y.mean()
            ms_o = P * ((Y.mean(1) - g) ** 2).sum() / (O - 1)
            ms_w = ((Y - Y.mean(1, keepdims=True)) ** 2).sum() / (O * (P - 1))
            ms_p = O * ((Y.mean(0) - g) ** 2).sum() / (P - 1)
            resid = Y - Y.mean(1, keepdims=True) - Y.mean(0, keepdims=True) + g
            ms_r = (resid ** 2).sum() / ((O - 1) * (P - 1))
            # rounding noise (e.g. area, which placement does not change) counts as zero
            eps = 1e-18 * g * g
            ms_w = 0.0 if ms_w <= eps else ms_w
            ms_r = 0.0 if ms_r <= eps else ms_r
            ms_p = 0.0 if ms_p <= eps else ms_p
            res['nested'] = {'orders': O, 'placements': P, 'ms_order': float(ms_o), 'ms_within': float(ms_w),
                             's2_order': float((ms_o - ms_w) / P), 's2_place': float(ms_w),
                             'F_order': float(ms_o / ms_w) if ms_w > 0 else None,
                             'p_order': float(stats.f.sf(ms_o / ms_w, O - 1, O * (P - 1))) if ms_w > 0 else None}
            res['crossed_check'] = {'ms_setting': float(ms_p), 'ms_resid': float(ms_r),
                                    'F_setting': float(ms_p / ms_r) if ms_r > 0 else None,
                                    'p_setting': float(stats.f.sf(ms_p / ms_r, P - 1, (O - 1) * (P - 1)))
                                    if ms_r > 0 else None}
        return res

    def units_subset(self, m, orders=None, placements=None):
        """Units of measure m restricted to some orders / placement settings (None if any is missing).
        Free flows: one mean per listed order over the listed placements; preserve: one per placement."""
        od = self.orders()
        if self.flow == 'preserve':
            ps = sorted(od[0]) if placements is None else placements
            if any(p not in od[0] for p in ps):
                return None
            return np.array([od[0][p][m] for p in ps])
        os_ = sorted(od) if orders is None else orders
        out = []
        for o in os_:
            if o not in od:
                return None
            ps = sorted(od[o]) if placements is None else placements
            if any(p not in od[o] or m not in od[o][p] for p in ps):
                return None
            out.append(np.mean([od[o][p][m] for p in ps]))
        return np.array(out)


def load():
    rows = list(csv.DictReader(open(RES / 'table.csv')))
    seeds = list(csv.DictReader(open(RES / 'seeds.csv')))
    runs, info = {}, {}
    for r in rows:
        if r.get('dup_of'):
            continue
        info[r['circuit']] = r
        k = (r['circuit'], r['platform'], r['flow'])
        runs[k] = Runs(r['flow'])
        runs[k].add(0, 0, vals_of(r))
    for s in seeds:
        # (order, placement) from the statement_order / placement columns when present
        s['_cell'] = (int(s['statement_order']), int(s['placement'])) \
            if s.get('statement_order') not in (None, '') and s.get('placement') not in (None, '') else cell(s['variant'])
    for s in sorted(seeds, key=lambda s: (s['circuit'], s['platform'], s['flow'], s['_cell'], s['variant'])):
        k = (s['circuit'], s['platform'], s['flow'])
        if k in runs:
            runs[k].add(*s['_cell'], vals_of(s))
    return runs, info


def vals_of(r):
    """The measures of a run, plus the synthesis-stage delay (OpenSTA before placement) when known."""
    v = {m: float(r[m]) for m in MEAS}
    if r.get('delay_synth') not in (None, ''):
        v['delay_synth'] = float(r['delay_synth'])
    return v


def usable(rn):
    """Enough runs for the hierarchy: >= 3 units (orders for free flows, placements for preserve)."""
    if rn is None:
        return False
    if rn.flow == 'preserve':
        return rn.nruns() >= 3
    return len(rn.orders()) >= 3


def r6(x):
    return None if x is None else float('%.6g' % x)


def main():
    warnings.simplefilter('ignore')      # constant groups (preserve area) in f_oneway / ttest_ind
    runs, info = load()
    why = {}
    for line in open(HERE / 'lists' / 'seeds.txt'):
        f, _, w = line.partition('#')
        why[pathlib.Path(f.strip()).name[:-len('.circ.txt')]] = w.strip()
    seeded = {c for (c, p, f), rn in runs.items() if usable(rn)}
    S = {}

    def summ(c, p, f, m):
        k = (c, p, f, m)
        if k not in S:
            rn = runs.get((c, p, f))
            S[k] = rn.summary(m) if usable(rn) else None
        return S[k]

    # ---- design and noise -------------------------------------------------------------------
    design = collections.Counter()
    dups = mismatch = 0
    for (c, p, f), rn in sorted(runs.items()):
        if rn.nruns() > 1:
            design['%s|%s|%s' % (p, f, ' '.join('o%d:p%s' % (o, ','.join(map(str, sorted(ps))))
                                                for o, ps in sorted(rn.orders().items())))] += 1
        dups += rn.dups
        mismatch += rn.dup_mismatch
    noise = {}
    for p, f in CONFIGS:
        for m in MEAS:
            cvp, cvo, cvs, cvold, neg = [], [], [], [], 0
            for c in sorted(seeded):
                s = summ(c, p, f, m)
                if not s:
                    continue
                mu = s['mean']
                if s['s2_place'] is not None:
                    cvp.append(np.sqrt(s['s2_place']) / mu)
                if s['s2_order'] is not None:
                    cvo.append(np.sqrt(max(s['s2_order'], 0)) / mu)
                    neg += s['s2_order'] < 0
                if s['sd_single_run'] is not None:
                    cvs.append(s['sd_single_run'] / mu)
                if s['old']['sd'] is not None:
                    cvold.append(s['old']['sd'] / s['old']['mean'])
            if not cvp:
                continue
            noise['%s|%s|%s' % (p, f, m)] = {
                'circuits': len(cvp), 'median_cv_place': r6(np.median(cvp)),
                'median_cv_order': r6(np.median(cvo)) if cvo else None,
                'order_var_estimate_negative': int(neg),
                'median_cv_single_run': r6(np.median(cvs)) if cvs else None,
                'old_median_cv_pooled_runs': r6(np.median(cvold))}

    # balanced cores (follow-up grids): two-level nested decomposition and the crossed check
    balanced = {}
    for c in sorted(seeded):
        for p, f in CONFIGS:
            for m in MEAS:
                s = summ(c, p, f, m)
                if s and s.get('nested'):
                    mu = s['mean']
                    balanced['%s|%s|%s|%s' % (c, p, f, m)] = {
                        'orders': s['balanced']['orders'], 'placements': s['balanced']['placements'],
                        'cv_order': r6(np.sqrt(max(s['nested']['s2_order'], 0)) / mu),
                        'cv_place': r6(np.sqrt(s['nested']['s2_place']) / mu),
                        **{k2: r6(v) for k2, v in s['nested'].items() if k2 not in ('orders', 'placements')},
                        **{k2: r6(v) for k2, v in s['crossed_check'].items()}}
    bsum = {}
    for p, f in CONFIGS:
        for m in MEAS:
            vs = [v for k2, v in balanced.items() if k2.endswith('|%s|%s|%s' % (p, f, m))]
            if not vs:
                continue
            so = [max(v['s2_order'], 0) for v in vs]
            sp = [v['s2_place'] for v in vs]
            share = [a / (a + b) for a, b in zip(so, sp) if a + b > 0]
            bsum['%s|%s|%s' % (p, f, m)] = {
                'circuits': len(vs), 'grid': '%dx%d' % (len(vs[0]['orders']), len(vs[0]['placements'])),
                'median_cv_order': r6(np.median([v['cv_order'] for v in vs])),
                'median_cv_place': r6(np.median([v['cv_place'] for v in vs])),
                'median_order_share': r6(np.median(share)) if share else None,
                # on relative variances (CV^2), pooled over the circuits
                'pooled_order_share': r6(sum(v['cv_order'] ** 2 for v in vs) /
                                         sum(v['cv_order'] ** 2 + v['cv_place'] ** 2 for v in vs))
                if sum(v['cv_order'] ** 2 + v['cv_place'] ** 2 for v in vs) > 0 else None,
                'order_effect_p_lt_0.05': sum(1 for v in vs if v['p_order'] is not None and v['p_order'] < ALPHA),
                'setting_effect_p_lt_0.05': sum(1 for v in vs if v['p_setting'] is not None and v['p_setting'] < ALPHA),
                'with_placement_variance': sum(1 for v in vs if v['p_order'] is not None)}

    # ---- groups -----------------------------------------------------------------------------
    iso_keys = {(w.split()[1], w.split()[2]) for w in why.values() if w.startswith('iso')}
    groups = collections.defaultdict(set)
    for c in seeded:
        r = info[c]
        if (r['function'], r['key']) in iso_keys:
            groups[(r['function'], r['key'])].add(c)

    def anova(ss):
        grand = np.concatenate(ss)
        if np.ptp(grand) == 0:
            return None
        with np.errstate(all='ignore'):
            F, pv = stats.f_oneway(*ss)
        ns = np.array([len(s) for s in ss], dtype=float)
        n0 = (ns.sum() - (ns ** 2).sum() / ns.sum()) / (len(ss) - 1)     # = n when every circuit has n units
        msb = sum(len(s) * (s.mean() - grand.mean()) ** 2 for s in ss) / (len(ss) - 1)
        msw = sum(((s - s.mean()) ** 2).sum() for s in ss) / (len(grand) - len(ss))
        icc = (msb - msw) / (msb + (n0 - 1) * msw) if msb + (n0 - 1) * msw > 0 else 1.0
        return {'F': float(F) if np.isfinite(F) else None, 'p': float(pv) if np.isfinite(pv) else 0.0,
                'icc': float(icc), 'n0': float(n0), 'msb': float(msb), 'msw': float(msw)}

    gout = []
    for (fn, k), cs in sorted(groups.items()):
        cs = sorted(cs)
        if len(cs) < 3:
            continue
        for p, f in CONFIGS:
            for m in ('delay', 'power', 'adp', 'area'):
                sm = [(c, summ(c, p, f, m)) for c in cs]
                sm = [(c, s) for c, s in sm if s]
                if len(sm) < 3:
                    continue
                new = anova([s['units'] for _, s in sm])
                old = anova([np.array([v[m] for _, v in sorted(runs[(c, p, f)].grid.items())]) for c, _ in sm])
                if new is None:
                    continue
                # variance components of one run: circuit, order (free flows), placement
                s2p = float(np.mean([s['s2_place'] for _, s in sm if s['s2_place'] is not None]))
                if f == 'preserve':
                    s2o = 0.0
                else:
                    inv = float(np.mean([np.mean([1.0 / len(v) for v in s['design'].values()]) for _, s in sm]))
                    s2o = new['msw'] - s2p * inv
                s2c = (new['msb'] - new['msw']) / new['n0']
                tot = max(s2c, 0) + max(s2o, 0) + s2p
                means = sorted((s['mean'], c) for c, s in sm)
                gout.append({'function': fn, 'key': k, 'platform': p, 'flow': f, 'measure': m,
                             'unit': sm[0][1]['unit'], 'circuits': len(sm), 'units_per_circuit': new['n0'],
                             'F': r6(new['F']), 'p': r6(new['p']), 'icc': r6(new['icc']),
                             'share_circuit_single_run': r6(max(s2c, 0) / tot) if tot > 0 else 1.0,
                             'share_order_single_run': r6(max(s2o, 0) / tot) if tot > 0 else 0.0,
                             'share_place_single_run': r6(s2p / tot) if tot > 0 else 0.0,
                             'old_pooled': {'runs_per_circuit': old['n0'], 'F': r6(old['F']), 'p': r6(old['p']),
                                            'icc': r6(old['icc'])} if old else None,
                             'best': means[0][1], 'best_mean': r6(means[0][0]),
                             'worst': means[-1][1], 'worst_mean': r6(means[-1][0]),
                             'spread': r6(means[-1][0] / means[0][0] - 1)})

    # ---- inversions -------------------------------------------------------------------------
    a = json.loads((RES / 'analysis.json').read_text())
    best = {}
    for t in a['inversions_top']:
        if t['measure'] == 'area' and t['flow'] == 'preserve':
            continue
        k = (t['function'], t['platform'], t['flow'], t['measure'])
        if k not in best or t['gain'] > best[k]['gain']:
            best[k] = t
    pairs = collections.OrderedDict()      # (worse, better, measure) -> found_in list
    meta = {}
    for k, t in sorted(best.items()):
        b, g = t['worse_logically'], t['better_logically']
        if b not in seeded or g not in seeded:
            continue
        pairs.setdefault((b, g, k[3]), []).append('%s %s %s %s' % k)
        meta.setdefault((b, g, k[3]), t)
    tests = []
    iout = []
    for (b, g, m), found in pairs.items():
        t = meta[(b, g, m)]
        res = {'worse_logically': b, 'key_worse': t['key_worse'], 'better_logically': g,
               'key_better': t['key_better'], 'measure': m, 'found_in': found, 'configs': {}}
        for p, f in CONFIGS:
            sb, sg = summ(b, p, f, m), summ(g, p, f, m)
            if not sb or not sg:
                continue
            xb, xg = sb['units'], sg['units']
            gain = 1 - xb.mean() / xg.mean()
            pw = welch_p(xb, xg, gain)
            pp, pmin = perm_p(xb, xg)
            ob = np.array([v[m] for _, v in sorted(runs[(b, p, f)].grid.items())])
            og = np.array([v[m] for _, v in sorted(runs[(g, p, f)].grid.items())])
            ogain = 1 - ob.mean() / og.mean()
            opw = welch_p(ob, og, ogain)
            cfg = {'unit': sb['unit'], 'n': [len(xb), len(xg)], 'gain': r6(gain), 'p_welch': r6(pw),
                   'p_perm': r6(pp), 'p_perm_min': r6(pmin),
                   'holds_welch': bool(pw < ALPHA and gain > 0),
                   'holds_perm': bool(pp <= ALPHA + 1e-12 and gain > 0),
                   'old_pooled': {'n': [len(ob), len(og)], 'gain': r6(ogain), 'p_welch': r6(opw),
                                  'holds': bool(opw < ALPHA and ogain > 0)}}
            res['configs']['%s/%s' % (p, f)] = cfg
            tests.append(cfg)
        iout.append(res)
    # Welch: Holm over every test of the table (all pair-measures x configurations)
    for c, x in zip(tests, holm([c['p_welch'] for c in tests])):
        c['p_welch_holm'] = r6(x)
        c['holds_welch_holm'] = bool(x < ALPHA and c['gain'] > 0)
    # permutation: Holm within each pair-measure over its configurations only (a family of 132 could
    # never pass: 132 x 1/924 > 0.05); floor 6 x 1/924 = 0.0065 for 6 v 6, 6 x 0.05 for 3 v 3
    for r in iout:
        cs = list(r['configs'].values())
        for c, y in zip(cs, holm([c['p_perm'] for c in cs])):
            c['p_perm_holm_in_pair'] = r6(y)
            c['holds_perm_holm_in_pair'] = bool(y <= ALPHA + 1e-12 and c['gain'] > 0)
    crit = ('old_pooled', 'holds_welch', 'holds_perm', 'holds_welch_holm', 'holds_perm_holm_in_pair')

    def nholds(r, cr):
        return sum(v['old_pooled']['holds'] if cr == 'old_pooled' else v[cr] for v in r['configs'].values())
    for r in iout:
        r['holds_in'] = {cr: nholds(r, cr) for cr in crit}
        r['configs_tested'] = len(r['configs'])
    # "holds in all six configurations" as one claim per pair-measure: intersection-union test
    # (p = the largest of its six one-sided p), Holm over every pair-measure tested in all six
    full = [r for r in iout if r['configs_tested'] == len(CONFIGS)]
    for key in ('welch', 'perm'):
        ps = [max(v['p_' + key] if v['gain'] > 0 else 1.0 for v in r['configs'].values()) for r in full]
        for r, p0, ph in zip(full, ps, holm(ps)):
            r['all_six_p_%s' % key] = r6(p0)
            r['all_six_p_%s_holm' % key] = r6(ph)
    # histogram by distinct (worse, better) pair, on its alphabetically first measure (the README's)
    first = {}
    for r in iout:
        first.setdefault((r['worse_logically'], r['better_logically']), r)
    hist = {cr: dict(sorted(collections.Counter(r['holds_in'][cr] for r in first.values()).items(), reverse=True))
            for cr in crit}

    # ---- first pair -------------------------------------------------------------------------
    fp = {}
    for c in FIRST_PAIR:
        for p, f in CONFIGS:
            for m in MEAS:
                s = summ(c, p, f, m)
                if not s:
                    continue
                fp['%s|%s|%s|%s' % (c, p, f, m)] = {
                    'unit': s['unit'], 'n_eff': s['n_eff'], 'mean': r6(s['mean']), 'sd_unit': r6(s['sd_unit']),
                    'sd_place': r6(np.sqrt(s['s2_place'])) if s['s2_place'] is not None else None,
                    'sd_order': r6(np.sqrt(max(s['s2_order'], 0))) if s['s2_order'] is not None else None,
                    'sd_single_run': r6(s['sd_single_run']),
                    'old_pooled': {k2: r6(v) for k2, v in s['old'].items()}}
    fptests = {}
    for p, f in CONFIGS:
        for m in MEAS:
            sa, sb = summ(FIRST_PAIR[0], p, f, m), summ(FIRST_PAIR[1], p, f, m)
            if sa and sb and np.ptp(np.concatenate([sa['units'], sb['units']])) > 0:
                xa, xb = sa['units'], sb['units']
                d = 1 - sa['mean'] / sb['mean']
                if np.ptp(xa) == 0 and np.ptp(xb) == 0:
                    pw = 0.0
                else:
                    pw = float(stats.ttest_ind(xa, xb, equal_var=False).pvalue)
                lo, floor = perm_p(xa, xb)
                hi, _ = perm_p(xb, xa)
                # the benchmark's single run (o0p0) of each circuit
                ba = runs[(FIRST_PAIR[0], p, f)].grid[(0, 0)][m]
                bb = runs[(FIRST_PAIR[1], p, f)].grid[(0, 0)][m]
                fptests['%s|%s|%s' % (p, f, m)] = {
                    'unit': sa['unit'], 'n': [len(xa), len(xb)], 'gain_ours': r6(d),
                    'single_run_gain_ours': r6(1 - ba / bb),
                    'p_welch_two_sided': r6(pw), 'p_perm_two_sided': r6(min(1.0, 2 * min(lo, hi))),
                    'p_perm_floor_two_sided': r6(2 * floor)}
    fk = list(fptests)
    # Welch, Holm over the first pair's tests; the permutation p is reported raw (two-sided floor
    # 2/924 = 0.0022 for 6 v 6, so it could not pass a Holm family of 24)
    for k2, x in zip(fk, holm([fptests[k]['p_welch_two_sided'] for k in fk])):
        v = fptests[k2]
        v['p_welch_holm'] = r6(x)
        same = (v['gain_ours'] > 0) == (v['single_run_gain_ours'] > 0)
        v['single_run_direction'] = ('confirmed' if same and x < ALPHA else
                                     'reversed' if not same and x < ALPHA else 'within noise')

    # ---- the README's exact comparisons, and a sensitivity analysis on fresh data -------------
    for r in iout:
        r['readme_exact'] = (short(r['worse_logically']), r['measure']) in EXACT
    fresh = {}
    for name, (fo, fpl, what) in SCEN.items():
        ftests, fout = [], []
        for r in iout:
            b, g, m = r['worse_logically'], r['better_logically'], r['measure']
            res = {'worse_logically': b, 'better_logically': g, 'measure': m, 'readme_exact': r['readme_exact'],
                   'configs': {}}
            for p, f in CONFIGS:
                rb, rg = runs.get((b, p, f)), runs.get((g, p, f))
                if not rb or not rg:
                    continue
                if f == 'preserve':
                    xb, xg = rb.units_subset(m, placements=fpl), rg.units_subset(m, placements=fpl)
                else:
                    xb, xg = rb.units_subset(m, fo, FRESH_PL), rg.units_subset(m, fo, FRESH_PL)
                if xb is None or xg is None:
                    continue
                gain = 1 - xb.mean() / xg.mean()
                pw = welch_p(xb, xg, gain)
                c = {'n': [len(xb), len(xg)], 'gain': r6(gain), 'p_welch': r6(pw), 'holds_welch': bool(pw < ALPHA and gain > 0)}
                res['configs']['%s/%s' % (p, f)] = c
                ftests.append(c)
            fout.append(res)
        for c, x in zip(ftests, holm([c['p_welch'] for c in ftests])):
            c['p_welch_holm'] = r6(x)
            c['holds_welch_holm'] = bool(x < ALPHA and c['gain'] > 0)
        ffull = [r for r in fout if len(r['configs']) == len(CONFIGS)]
        ps = [max(v['p_welch'] if v['gain'] > 0 else 1.0 for v in r['configs'].values()) for r in ffull]
        for r, p0, ph in zip(ffull, ps, holm(ps)):
            r['all_six_p_welch'], r['all_six_p_welch_holm'] = r6(p0), r6(ph)
        for r in fout:
            r['holds_in'] = {cr: sum(v[cr] for v in r['configs'].values()) for cr in ('holds_welch', 'holds_welch_holm')}
            r['configs_tested'] = len(r['configs'])
        ffirst = {}
        for r in fout:
            ffirst.setdefault((r['worse_logically'], r['better_logically']), r)
        fresh[name] = {'what': what, 'tests': len(ftests), 'all_six_claims': len(ffull), 'pairs': fout,
                       'histogram_by_pair': {cr: dict(sorted(collections.Counter(
                           r['holds_in'][cr] for r in ffirst.values() if r['configs_tested'] == len(CONFIGS)).items(),
                           reverse=True)) for cr in ('holds_welch', 'holds_welch_holm')},
                       'pairs_with_all_configs': sum(1 for r in ffirst.values() if r['configs_tested'] == len(CONFIGS))}

    # ---- cross-order prediction: synthesis-stage delay of some orders vs routed delay of others --
    def rho(x, y):
        if len(x) < 4 or np.ptp(x) == 0 or np.ptp(y) == 0:
            return None
        v = stats.spearmanr(x, y)[0]
        return float(v) if np.isfinite(v) else None

    def mean_or_none(v):
        v = [x for x in v if x is not None]
        return float(np.mean(v)) if v else None

    def per_unit(rn, kind, unit):
        """(synthesis-stage delay, routed delay) of one order (free) or placement (preserve)."""
        od = rn.orders()
        if rn.flow == 'preserve':
            v = od[0].get(unit)
            return None if v is None or 'delay_synth' not in v else (v['delay_synth'], v['delay'])
        if unit not in od:
            return None
        ps = sorted(od[unit]) if kind == 'group' else [p for p in FRESH_PL if p in od[unit]]
        if not ps or any('delay_synth' not in od[unit][p] for p in ps) or (kind != 'group' and len(ps) < len(FRESH_PL)):
            return None
        return np.mean([od[unit][p]['delay_synth'] for p in ps]), np.mean([od[unit][p]['delay'] for p in ps])

    def splits(units, kind):
        """(A, B) pairs: groups: A = k units, B = all the others; balanced: B = 3 units, A = k of the rest."""
        out = collections.defaultdict(list)
        if kind == 'group':
            for k in range(1, len(units)):
                for A in itertools.combinations(units, k):
                    out[k].append((A, tuple(u for u in units if u not in A)))
        else:
            for B in itertools.combinations(units, 3):
                rest = [u for u in units if u not in B]
                for k in range(1, len(rest) + 1):
                    for A in itertools.combinations(rest, k):
                        out[k].append((A, B))
        return out

    def predict_sets(cs, p, f, kind):
        rns = [runs[(c, p, f)] for c in cs]
        if f == 'preserve':
            units = sorted(set.intersection(*(set(rn.orders()[0]) for rn in rns)))
        else:
            units = sorted(set.intersection(*(set(rn.orders()) for rn in rns)))
        data = {}
        for c, rn in zip(cs, rns):
            d = {u: per_unit(rn, kind, u) for u in units}
            if any(v is None for v in d.values()):
                return None, None
            data[c] = d
        if len(units) < 2:
            return None, None
        res = {}
        for k, sp in splits(units, kind).items():
            cross, same, ceil = [], [], []
            for A, B in sp:
                sA = [np.mean([data[c][u][0] for u in A]) for c in cs]
                rA = [np.mean([data[c][u][1] for u in A]) for c in cs]
                rB = [np.mean([data[c][u][1] for u in B]) for c in cs]
                cross.append(rho(sA, rB))
                same.append(rho(sA, rA))
                ceil.append(rho(rA, rB))
            res[k] = {'cross': mean_or_none(cross), 'same_run': mean_or_none(same), 'ceiling': mean_or_none(ceil),
                      'splits': len(sp), 'test_units': len(sp[0][1])}
        # the selection order alone: A = (order 0), B = every other order
        if f != 'preserve' and kind == 'group' and 0 in units:
            B = tuple(u for u in units if u != 0)
            res['order0'] = {'cross': rho([data[c][0][0] for c in cs], [np.mean([data[c][u][1] for u in B]) for c in cs]),
                             'same_run': rho([data[c][0][0] for c in cs], [data[c][0][1] for c in cs]),
                             'ceiling': rho([data[c][0][1] for c in cs], [np.mean([data[c][u][1] for u in B]) for c in cs])}
        return units, res

    xorder = {'groups': {}, 'balanced_within_function': {}}
    for p, f in CONFIGS:
        acc = collections.defaultdict(lambda: collections.defaultdict(list))
        ng = 0
        for (fn, k0), cs in sorted(groups.items()):
            cs = sorted(c for c in cs if (c, p, f) in runs and usable(runs[(c, p, f)]))
            if len(cs) < 4:
                continue
            units, res = predict_sets(cs, p, f, 'group')
            if res is None:
                continue
            ng += 1
            for k, v in res.items():
                for q in ('cross', 'same_run', 'ceiling'):
                    if v[q] is not None:
                        acc[k][q].append(v[q])
        if ng:
            xorder['groups']['%s|%s' % (p, f)] = {
                'groups': ng, 'explain_same_run_base': r6(a.get('explain', {}).get('%s|%s|delay' % (p, f), {})
                                                           .get('delay_synth', {}).get('mean_rho')),
                **{str(k): {q: r6(np.mean(v)) if v else None for q, v in d.items()} for k, d in sorted(acc.items(), key=str)}}
        accb = collections.defaultdict(lambda: collections.defaultdict(list))
        nf = 0
        byfn = collections.defaultdict(list)
        for (c, pp, ff), rn in sorted(runs.items()):
            if (pp, ff) == (p, f) and c in info and (rn.balanced_core() or (f == 'preserve' and rn.nruns() >= 6)):
                byfn[info[c]['function']].append(c)
        for fn, cs in sorted(byfn.items()):
            if len(cs) < 4:
                continue
            units, res = predict_sets(cs, p, f, 'balanced')
            if res is None:
                continue
            nf += 1
            for k, v in res.items():
                for q in ('cross', 'same_run', 'ceiling'):
                    if v[q] is not None:
                        accb[k][q].append(v[q])
        if nf:
            xorder['balanced_within_function']['%s|%s' % (p, f)] = {
                'functions': nf, 'circuits': sum(len(v) for v in byfn.values() if len(v) >= 4),
                **{str(k): {q: r6(np.mean(v)) if v else None for q, v in d.items()} for k, d in sorted(accb.items(), key=str)}}

    # ---- noise ratios and the beyond-noise thresholds -----------------------------------------
    ratios = {}
    for p, f in CONFIGS:
        if f == 'preserve':
            continue
        n_all = noise.get('%s|%s|delay' % (p, f), {})
        b = bsum.get('%s|%s|delay' % (p, f), {})
        thr = {}
        for m in ('delay', 'adp'):
            v = a['noise'].get('synth|%s|%s|%s' % (p, f, m), {})
            if 'median_cv_unbiased' in v:
                thr[m] = r6(2 * np.sqrt(2) * v['median_cv_unbiased'])
        ratios['%s|%s' % (p, f)] = {
            'delay_order_over_place_all': r6(n_all['median_cv_order'] / n_all['median_cv_place'])
            if n_all.get('median_cv_order') and n_all.get('median_cv_place') else None,
            'delay_order_over_place_balanced': r6(b['median_cv_order'] / b['median_cv_place'])
            if b.get('median_cv_order') and b.get('median_cv_place') else None,
            'single_run_threshold': thr}

    # ---- observations -----------------------------------------------------------------------
    obs = {}
    for (c, p, f), rn in sorted(runs.items()):
        if c in seeded and rn.nruns() > 1:
            obs['%s|%s|%s' % (c, p, f)] = {str(o): {str(pl): [v[m] for m in MEAS] for pl, v in sorted(ps.items())}
                                           for o, ps in sorted(rn.orders().items())}
    about = {
        'cells': 'base = o0p0, pnrK = o0pK, synthK = oKpK, oOpP = (order O, placement setting P)',
        'free_flow_unit': 'order mean (mean of the placements of one statement order); circuits summarised by '
                          'the mean of their order means (orders weighted equally); n_eff = number of orders',
        'preserve_unit': 'placement run (one netlist; one run per placement setting)',
        'order_variance': 's2_order = var(order means) - s2_place * mean(1/n_o); s2_place = pooled within-order '
                          'variance; balanced core (>= 3 orders x >= 2 common settings) used when present',
        'tests': 'one-sided Welch t and exact permutation (difference of means, all splits) on the units. '
                 'Welch, Holm: over every (pair, measure, configuration) test of the inversions table. '
                 'Permutation, Holm: within each pair-measure over its configurations. All six: '
                 'intersection-union p (largest of the six), Holm over the 22 pair-measures (19 pairs)',
        'old_pooled': 'every run as an independent observation (the previous analysis), for comparison',
        'observations': 'circuit|library|flow -> order -> placement setting -> [%s]' % ', '.join(MEAS),
        'duplicate_jobs_ignored': dups, 'duplicate_jobs_with_different_values': mismatch}
    out = {'about': about, 'design': dict(sorted(design.items())), 'noise': noise,
           'balanced_summary': bsum, 'balanced': balanced,
           'groups': gout,
           'inversions': iout, 'inversion_tests': len(tests), 'inversion_histogram_by_pair': hist,
           'fresh_data': fresh, 'cross_order_prediction': xorder, 'free_flow_noise_ratio_and_thresholds': ratios,
           'first_pair': fp, 'first_pair_tests': fptests}
    text = json.dumps(out, indent=1)
    text = text[:text.rindex('}')].rstrip() + ',\n "observations": {\n' + ',\n'.join(
        '  %s: %s' % (json.dumps(k), json.dumps(v, separators=(',', ':'))) for k, v in obs.items()) + '\n }\n}\n'
    json.loads(text)
    (RES / 'seeded.json').write_text(text)

    # ---- markdown ---------------------------------------------------------------------------
    md = ['# Repeated runs (generated by seeded.py)', '',
          'Each run is a cell (O, P): statement order O, placement setting P (base = o0p0, pnrK = o0pK, '
          'synthK = oKpK). **Units:** free flows (free, free-area): the *order mean* (mean of the placements '
          'of one order), orders weighted equally, n = number of orders. Preserve: one run per placement '
          'setting of the single netlist. *Old* = every run pooled as independent (order 0 weighted 4:1:1), '
          'kept for comparison. **Significance:** a result is called supported only when it passes the Holm '
          'family named in its section (Welch, Holm unless stated); raw p < 0.05 alone is exploratory. Tests on '
          '3 order means (Welch with 2-4 degrees of freedom; permutation floor 0.05) are exploratory. The '
          'inversion pairs were chosen on the base run o0p0 and the balanced circuits after the first repeats '
          'were seen, so "Fresh data" repeats the inversion tests without those runs.', '',
          '## Design', '', '| Library | Flow | grid (order: placement settings) | circuits |', '|---|---|---|---:|']
    for k, v in sorted(design.items()):
        p, f, gtxt = k.split('|')
        md.append('| %s | %s | %s | %d |' % (p, f, gtxt, v))
    md += ['', '## Noise components (median over repeated circuits, CV = sd / mean)', '',
           'place: pooled within-order sd. order: sqrt of the order variance (moments estimate; negative -> 0, '
           'count shown). single run: sqrt(order + place), the noise of one benchmark run. old: sd of all runs pooled.', '',
           '| Library | Flow | measure | circuits | place CV | order CV | order var < 0 | single-run CV | old pooled CV |',
           '|---|---|---|---:|---:|---:|---:|---:|---:|']

    def pc(x, d=2):
        return '—' if x is None else '%.*f%%' % (d, 100 * x)
    for k, v in noise.items():
        p, f, m = k.split('|')
        md.append('| %s | %s | %s | %d | %s | %s | %s | %s | %s |' % (
            p, f, m, v['circuits'], pc(v['median_cv_place']), pc(v['median_cv_order']),
            v['order_var_estimate_negative'] if f != 'preserve' else '—', pc(v['median_cv_single_run']),
            pc(v['old_median_cv_pooled_runs'])))
    if balanced:
        md += ['', '## Balanced grids: two-level decomposition (orders; placements within orders)', '',
               'Nested ANOVA on the balanced core of each circuit (o0p3 left out), summarised over the circuits '
               'with a balanced grid (per circuit in seeded.json, "balanced"): median order and placement CV; '
               'order share of a single run\'s variance (median over circuits, and pooled on CV²); circuits with '
               'an order effect (F test p < 0.05); and the crossed check: circuits where a placement-setting '
               'effect shared by all orders has p < 0.05 (about 5% expected by chance if there is none).', '',
               '| Library | Flow | measure | circuits | grid | order CV | place CV | order share (median / pooled) | '
               'order effect p < 0.05 | setting effect p < 0.05 |',
               '|---|---|---|---:|---|---:|---:|---|---:|---:|']
        for k, v in bsum.items():
            p, f, m = k.split('|')
            md.append('| %s | %s | %s | %d | %s | %s | %s | %s / %s | %d / %d | %d / %d |' % (
                p, f, m, v['circuits'], v['grid'], pc(v['median_cv_order']), pc(v['median_cv_place']),
                '—' if v['median_order_share'] is None else '%.2f' % v['median_order_share'],
                '—' if v['pooled_order_share'] is None else '%.2f' % v['pooled_order_share'],
                v['order_effect_p_lt_0.05'], v['with_placement_variance'],
                v['setting_effect_p_lt_0.05'], v['with_placement_variance']))
    md += ['', '## Same-metric groups: structure against noise', '',
           'One-way ANOVA between the circuits of a group on the units above (free: order means, 3 per circuit or '
           '6 with a balanced grid; preserve: 4 or 6 runs; units = the ANOVA n0). ICC(1) on that unit; shares: variance components of a single run (circuit / order / '
           'placement). Old: ICC and p with every run pooled.', '',
           '| Function | key | Library | Flow | measure | circuits | units | spread | ICC | p | circuit share | order share | place share | old ICC | old p |',
           '|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for g in gout:
        if g['measure'] not in ('delay', 'power'):
            continue
        o = g['old_pooled'] or {}
        md.append('| %s | %s | %s | %s | %s | %d | %.3g | %.1f%% | %.2f | %.2g | %.2f | %.2f | %.2f | %s | %s |' % (
            g['function'], g['key'], g['platform'], g['flow'], g['measure'], g['circuits'], g['units_per_circuit'],
            100 * g['spread'], g['icc'], g['p'], g['share_circuit_single_run'], g['share_order_single_run'],
            g['share_place_single_run'], '%.2f' % o['icc'] if o else '—', '%.2g' % o['p'] if o else '—'))
    md += ['', '## Apparent dominance inversions under repeats', '',
           'The logically worse circuit (first) against the one dominating it, on the measure it was found on. '
           'gain = 1 - mean(worse) / mean(better) on the units. Each cell: gain, then marks: **W** Welch p < 0.05, '
           '**P** exact permutation p <= 0.05 (its floor is 1 / C(n1 + n2, n1): 0.05 for 3 vs 3, 0.014 for 4 vs 4, '
           '0.0011 for 6 vs 6), '
           '**H** Welch, Holm p < 0.05 (family: all %d tests of this table, every (pair, measure, '
           'configuration) below); o = old pooled Welch holds. Last column: configurations held by old / Welch / '
           'permutation / Welch, Holm (%d tests) / permutation, Holm within the pair-measure\'s own '
           'configurations (6 tests; floor 6/924 = 0.0065 for 6 v 6). * = a README "Exact comparison".'
           % (len(tests), len(tests)), '',
           '| worse (key) | better (key) | measure | ' + ' | '.join('%s/%s' % c for c in CONFIGS) +
           ' | holds: old / W / P / W-Holm / P-Holm in pair |',
           '|---|---|---|' + '---|' * 6 + '---|']
    for r in iout:
        cells = []
        for p, f in CONFIGS:
            v = r['configs'].get('%s/%s' % (p, f))
            if not v:
                cells.append('—')
                continue
            mk = ''.join(x for x, ok in (('W', v['holds_welch']), ('P', v['holds_perm']),
                                         ('H', v['holds_welch_holm']), ('o', v['old_pooled']['holds'])) if ok)
            cells.append('%+.1f%% %s (p %.2g)' % (100 * v['gain'], mk, v['p_welch']))
        h = r['holds_in']
        md.append('| %s%s (%s) | %s (%s) | %s | %s | %d / %d / %d / %d / %d of %d |' % (
            '*' if r['readme_exact'] else '', short(r['worse_logically'])[:46], r['key_worse'],
            short(r['better_logically'])[:46], r['key_better'],
            r['measure'], ' | '.join(cells), h['old_pooled'], h['holds_welch'], h['holds_perm'],
            h['holds_welch_holm'], h['holds_perm_holm_in_pair'], r['configs_tested']))
    nfirst = len(first)
    md += ['', '"Holds in all six configurations" as one claim per pair-measure: intersection-union p = the '
           'largest of its six one-sided p (1 if a gain is negative); Holm over the %d pair-measures (%d pairs) '
           'tested in all six, separately for Welch and for permutation.' % (len(full), nfirst), '',
           '| worse | better | measure | gain range | max Welch p | Welch, Holm (%d) | max permutation p | '
           'permutation, Holm (%d) |' % (len(full), len(full)),
           '|---|---|---|---|---:|---:|---:|---:|']
    for r in full:
        gs = [v['gain'] for v in r['configs'].values()]
        md.append('| %s%s | %s | %s | %+.1f%% to %+.1f%% | %.2g | %.2g | %.2g | %.2g |' % (
            '*' if r['readme_exact'] else '', short(r['worse_logically'])[:46], short(r['better_logically'])[:46],
            r['measure'], 100 * min(gs), 100 * max(gs), r['all_six_p_welch'], r['all_six_p_welch_holm'],
            r['all_six_p_perm'], r['all_six_p_perm_holm']))
    md += ['', 'Distinct pairs (%d) by the number of configurations where the inversion holds (a pair found on '
           'two measures counted once, on its alphabetically first measure):' % nfirst, '',
           '| configurations | pooled runs (old method) | Welch | permutation | Welch, Holm (%d tests) | '
           'permutation, Holm within the pair (6 tests) |' % len(tests),
           '|---:|---:|---:|---:|---:|---:|']
    for n in range(6, -1, -1):
        md.append('| %d | %s |' % (n, ' | '.join(str(hist[cr].get(n, 0)) for cr in crit)))
    # fresh data
    md += ['', '## Fresh data: the inversion tests without the runs that chose them', '',
           'The same one-sided Welch tests on data the selection never saw. Welch, Holm over all tests of each '
           'scenario; all six = intersection-union p, Holm over the pair-measures tested in all six.', '']
    for name, fr in fresh.items():
        md += ['### %s' % name, '', fr['what'] + '; %d tests, %d all-six claims.' % (fr['tests'], fr['all_six_claims']), '',
               '| worse | better | measure | ' + ' | '.join('%s/%s' % c for c in CONFIGS) +
               ' | holds: Welch / Welch, Holm | all six: Welch, Holm |',
               '|---|---|---|' + '---|' * 6 + '---|---:|']
        for r in fr['pairs']:
            cells = []
            for p, f in CONFIGS:
                v = r['configs'].get('%s/%s' % (p, f))
                cells.append('—' if not v else '%+.1f%% %s (p %.2g; %dv%d)' % (
                    100 * v['gain'], ('W' if v['holds_welch'] else '') + ('H' if v['holds_welch_holm'] else ''),
                    v['p_welch'], v['n'][0], v['n'][1]))
            md.append('| %s%s | %s | %s | %s | %d / %d of %d | %s |' % (
                '*' if r['readme_exact'] else '', short(r['worse_logically'])[:46], short(r['better_logically'])[:46],
                r['measure'], ' | '.join(cells), r['holds_in']['holds_welch'], r['holds_in']['holds_welch_holm'],
                r['configs_tested'], '%.2g' % r['all_six_p_welch_holm'] if 'all_six_p_welch_holm' in r else '—'))
        md += ['', 'Pairs (%d with all six configurations) by configurations held:' % fr['pairs_with_all_configs'], '',
               '| configurations | Welch | Welch, Holm |', '|---:|---:|---:|']
        for n in range(6, -1, -1):
            md.append('| %d | %d | %d |' % (n, fr['histogram_by_pair']['holds_welch'].get(n, 0),
                                           fr['histogram_by_pair']['holds_welch_holm'].get(n, 0)))
        md.append('')
    # cross-order prediction
    md += ['## Does the synthesis-stage delay of some orders predict the routed delay of others?', '',
           'Spearman rho between the mean synthesis-stage delay (OpenSTA after Yosys + ABC, before placement) of k '
           'statement orders and the mean routed delay of other, disjoint orders; same run: against the routed '
           'delay of the same k orders; routed run (column "ceiling"): the routed delay of the k orders against that '
           'of the disjoint orders, i.e. what a whole routed run of those orders achieves (itself noisy, so not an '
           'upper bound for every predictor). Preserve: placements stand in for orders '
           '(one netlist, so the synthesis-stage delay is one value per circuit).', '']
    if not xorder['groups']:
        md += ['(no synthesis-stage delay in seeds.csv: section skipped)', '']
    else:
        md += ['### Within the repeated same-metric groups (mean over groups of the within-group rho)', '',
               'Free flows: 3 orders per circuit (order 0: 4 placements); k orders against all the others, '
               'averaged over the choices of the k; "order 0" = the base run\'s order against orders 1-2. '
               'explain: analyze.py\'s same-run rho on the base runs of every group with >= 5 members.', '',
               '| Library | Flow | groups | k | cross-order rho | same-run rho | ceiling | order 0: cross / same / ceiling | explain (base) |',
               '|---|---|---:|---|---:|---:|---:|---|---:|']

        def f2(x):
            return '—' if x is None else '%.2f' % x
        for key, v in xorder['groups'].items():
            p, f = key.split('|')
            o0 = v.get('order0', {})
            for k in sorted(x for x in v if x.isdigit()):
                md.append('| %s | %s | %d | %s v rest | %s | %s | %s | %s | %s |' % (
                    p, f, v['groups'], k, f2(v[k]['cross']), f2(v[k]['same_run']), f2(v[k]['ceiling']),
                    '%s / %s / %s' % (f2(o0.get('cross')), f2(o0.get('same_run')), f2(o0.get('ceiling')))
                    if o0 and k == '1' else '', f2(v['explain_same_run_base']) if k == '1' else ''))
        md += ['', '### Balanced circuits, across circuits within a function (mean over functions)', '',
               'Not same-metric groups: the circuits differ in their counts too, so rho here mixes structure and '
               'counts. Free flows: 6 orders x placements 0-2; every split into 3 test orders and k of the other '
               '3. Preserve: 6 placements, the same splits.', '',
               '| Library | Flow | functions | circuits | k | cross-order rho | same-run rho | ceiling |',
               '|---|---|---:|---:|---|---:|---:|---:|']
        for key, v in xorder['balanced_within_function'].items():
            p, f = key.split('|')
            for k in sorted(x for x in v if x.isdigit()):
                md.append('| %s | %s | %d | %d | %s v 3 | %s | %s | %s |' % (
                    p, f, v['functions'], v['circuits'], k, f2(v[k]['cross']), f2(v[k]['same_run']),
                    f2(v[k]['ceiling'])))
        md.append('')
    md += ['## Free flows: order against placement noise, and the single-run thresholds', '',
           'Delay order CV / placement CV (ratio of the medians: all repeated circuits; balanced circuits); '
           'beyond-noise threshold of one benchmark run against another (analyze.py: 2 sqrt 2 x median-unbiased '
           'CV of base + synth1 + synth2).', '',
           '| Library | Flow | delay order/place (all) | (balanced) | threshold delay | threshold ADP |',
           '|---|---|---:|---:|---:|---:|']
    for key, v in ratios.items():
        p, f = key.split('|')
        md.append('| %s | %s | %s | %s | %s | %s |' % (
            p, f, '—' if v['delay_order_over_place_all'] is None else '%.1f' % v['delay_order_over_place_all'],
            '—' if v['delay_order_over_place_balanced'] is None else '%.1f' % v['delay_order_over_place_balanced'],
            pc(v['single_run_threshold'].get('delay'), 1), pc(v['single_run_threshold'].get('adp'), 1)))
    md += ['', '## The benchmark\'s first pair', '',
           'mean: of the units (free: of the order means). sd unit: between those units. sd place / order / single '
           'run: the components. Old: mean and sd of all runs pooled.', '',
           '| circuit | Library | Flow | measure | n | mean | sd unit | sd place | sd order | sd single run | old mean ± sd (n) |',
           '|---|---|---|---|---:|---:|---:|---:|---:|---:|---|']
    for k, v in fp.items():
        c, p, f, m = k.split('|')
        o = v['old_pooled']

        def g4(x):
            return '—' if x is None else '%.4g' % x
        md.append('| %s | %s | %s | %s | %d | %s | %s | %s | %s | %s | %s ± %s (%d) |' % (
            c.split('--')[0], p, f, m, v['n_eff'], g4(v['mean']), g4(v['sd_unit']), g4(v['sd_place']),
            g4(v['sd_order']), g4(v['sd_single_run']), g4(o['mean']), g4(o['sd']), o['n']))
    md += ['', 'Ours against NIST: gain = 1 - ours / NIST on the units (n ours, n NIST); the benchmark\'s single run '
           '(o0p0) for comparison; two-sided Welch p and Welch, Holm over the %d rows of this table; the exact '
           'permutation p raw only (its two-sided floor, 2/924 for 6 v 6, cannot pass a Holm family of %d). '
           'Direction: confirmed / reversed = Welch, Holm p < 0.05 with the single run\'s sign / the other sign.'
           % (len(fptests), len(fptests)), '',
           '| Library | Flow | measure | unit (n) | gain | single run | Welch p | Welch, Holm | perm p (raw) | direction |',
           '|---|---|---|---|---:|---:|---:|---:|---:|---|']
    for k, v in fptests.items():
        p, f, m = k.split('|')
        md.append('| %s | %s | %s | %s (%d v %d) | %+.1f%% | %+.1f%% | %.2g | %.2g | %.2g | %s |' % (
            p, f, m, v['unit'], v['n'][0], v['n'][1], 100 * v['gain_ours'], 100 * v['single_run_gain_ours'],
            v['p_welch_two_sided'], v['p_welch_holm'], v['p_perm_two_sided'], v['single_run_direction']))
    (RES / 'SEEDED.md').write_text('\n'.join(md) + '\n')
    print('wrote', RES / 'SEEDED.md', len(gout), 'group rows', len(iout), 'pair-measures', len(tests), 'tests')


if __name__ == '__main__':
    main()
