#!/usr/bin/env python3
"""Analyses of the study (hardware/research/results/table.csv, seeds.csv) -> results/analysis.json.

    python3 hardware/research/analyze.py

  noise        seed-to-seed coefficient of variation per library, flow and measure (pnr seeds:
               placement parameters; synth seeds: RTL statement order + pnr), and the threshold
               used below: a relative difference counts as beyond noise if it exceeds
               Z * sqrt(2) * (median CV of that library/flow/measure)
  iso          same-metric groups: relative range of each measure, and how often it exceeds noise
  inversions   pairs where one circuit dominates the other in (A, AD, G, GD) but is physically
               worse; overall, beyond noise, and the largest ones
  synthesis    how often free synthesis maps different structures to the same netlist; rank
               agreement of each measure between flows and libraries
  predict      held-out ranking quality of abstract proxies, zero-fit physical proxies and a
               ridge model on the file features (split by circuit hash; same-metric groups kept
               whole; also leave-one-function-out)
"""
from __future__ import annotations

import collections
import csv
import hashlib
import itertools
import json
import math
import pathlib

import numpy as np
from scipy import stats

HERE = pathlib.Path(__file__).resolve().parent
RES = HERE / 'results'
Z = 2.0
MEASURES = ('area', 'delay', 'adp', 'power')
CONFIGS = [(p, f) for p in ('nangate45', 'sky130hd') for f in ('preserve', 'free', 'free-area')]
FUNCS = ('aes-sbox', 'aes-invsbox', 'aes-sbox-sel', 'aes-mixcolumns', 'aes-invmixcolumns')


def load():
    rows = list(csv.DictReader(open(RES / 'table.csv')))
    for r in rows:
        for k, v in r.items():
            if k.startswith(('f_', 'm_')) and k != 'm_hash' or k in (
                    'cells', 'area', 'delay_synth', 'delay_place', 'delay', 'adp', 'power',
                    'power_sw', 'wire', 'die'):
                r[k] = float(v)
    seeds = list(csv.DictReader(open(RES / 'seeds.csv'))) if (RES / 'seeds.csv').exists() else []
    for r in seeds:
        for k in ('area', 'delay', 'adp', 'power', 'wire', 'cells'):
            r[k] = float(r[k])
    return rows, seeds


def key4(r):
    return tuple(int(x) for x in r['key'].split('/'))


def dominates(a, b):
    return all(x <= y for x, y in zip(a, b)) and a != b


# ---- noise ---------------------------------------------------------------------------------

def noise(rows, seeds):
    base = {(r['circuit'], r['platform'], r['flow']): r for r in rows}
    groups = collections.defaultdict(list)
    for s in seeds:
        kind = 'synth' if s['variant'].startswith('synth') else 'pnr'
        groups[(kind, s['circuit'], s['platform'], s['flow'])].append(s)
    cv = collections.defaultdict(list)
    per = {}
    for (kind, c, p, f), ss in groups.items():
        b = base.get((c, p, f))
        if not b:
            continue
        for m in MEASURES:
            v = [b[m]] + [s[m] for s in ss]
            if len(v) < 3:
                continue
            mu = float(np.mean(v))
            sd = float(np.std(v, ddof=1))
            cv[(kind, p, f, m)].append(sd / mu)
            per[(kind, c, p, f, m)] = (mu, sd, len(v), min(v), max(v))
    summary = {'%s|%s|%s|%s' % k: {'n': len(v), 'median_cv': float(np.median(v)),
                                   'p90_cv': float(np.percentile(v, 90))} for k, v in cv.items()}

    def thr(p, f, m):
        # pnr noise for preserve (synthesis is deterministic and order-blind there), synth+pnr
        # noise for the free flows
        kind = 'pnr' if f == 'preserve' else 'synth'
        v = cv.get((kind, p, f, m)) or cv.get(('pnr', p, f, m))
        return Z * math.sqrt(2) * float(np.median(v)) if v else None
    return summary, thr, per


# ---- iso groups ----------------------------------------------------------------------------

_RQ = {}


def range_q95(n, trials=200000):
    """95% quantile of max - min of n independent standard normal samples (Monte Carlo)."""
    if n not in _RQ:
        x = np.random.default_rng(n).standard_normal((trials, n))
        _RQ[n] = float(np.quantile(x.max(1) - x.min(1), 0.95))
    return _RQ[n]


def iso(rows, thr):
    out = collections.defaultdict(list)
    groups = collections.defaultdict(list)
    for r in rows:
        groups[(r['function'], r['key'], r['platform'], r['flow'])].append(r)
    iso_keys = {(r['function'], r['key']) for r in rows if r['part'] == 'iso'}
    detail = []
    for (fn, k, p, f), rs in groups.items():
        if (fn, k) not in iso_keys or len(rs) < 4:
            continue
        for m in MEASURES:
            v = [r[m] for r in rs]
            med = float(np.median(v))
            rr = (max(v) - min(v)) / med
            t = thr(p, f, m)
            # beyond noise: the range exceeds the 95% quantile of the range of len(rs) circuits
            # that differ only by noise (normal, sd = the noise CV); exact for any n
            crit = None if t is None else range_q95(len(rs)) * t / (Z * math.sqrt(2))
            out[(p, f, m)].append((rr, crit))
            best = min(rs, key=lambda r: r[m])
            worst = max(rs, key=lambda r: r[m])
            detail.append({'function': fn, 'key': k, 'platform': p, 'flow': f, 'measure': m,
                           'n': len(rs), 'rel_range': rr, 'range_crit': crit,
                           'best': best['circuit'], 'best_value': best[m],
                           'worst': worst['circuit'], 'worst_value': worst[m],
                           'baseline_members': [r['circuit'] for r in rs if r['part'] == 'baseline'],
                           'baseline_rank': sorted(v).index(min(r[m] for r in rs if r['part'] == 'baseline'))
                           if any(r['part'] == 'baseline' for r in rs) else None})
    summ = {}
    for (p, f, m), v in out.items():
        rr = [a for a, _ in v]
        beyond = [a > t for a, t in v if t is not None]
        summ['%s|%s|%s' % (p, f, m)] = {'groups': len(v), 'median_rel_range': float(np.median(rr)),
                                        'max_rel_range': float(max(rr)),
                                        'beyond_noise': sum(beyond), 'with_threshold': len(beyond)}
    return summ, detail


# ---- dominance inversions -------------------------------------------------------------------

def inversions(rows, thr):
    by = collections.defaultdict(list)
    for r in rows:
        by[(r['function'], r['platform'], r['flow'])].append(r)
    summ, top = {}, []
    for (fn, p, f), rs in by.items():
        for m in MEASURES:
            t = thr(p, f, m)
            n = inv = sig = 0
            ex = []
            for a, b in itertools.permutations(rs, 2):
                ka, kb = key4(a), key4(b)
                if not dominates(ka, kb):
                    continue          # a is logically better than b
                n += 1
                if b[m] < a[m]:       # the logically worse b is physically better
                    inv += 1
                    rel = (a[m] - b[m]) / a[m]
                    if t is not None and rel > t:
                        sig += 1
                        ex.append((rel, b, a))
            summ['%s|%s|%s|%s' % (fn, p, f, m)] = {'pairs': n, 'inverted': inv,
                                                   'inverted_beyond_noise': sig,
                                                   'threshold': t}
            ex.sort(key=lambda x: -x[0])
            for rel, b, a in ex[:3]:
                top.append({'function': fn, 'platform': p, 'flow': f, 'measure': m,
                            'gain': rel, 'worse_logically': b['circuit'], 'key_worse': b['key'],
                            'value_worse': b[m], 'better_logically': a['circuit'],
                            'key_better': a['key'], 'value_better': a[m]})
    return summ, top


def best_vs_published(rows):
    """Per function and config and measure: is the physically best circuit of all also
    logically best among those beating the best published/NIST circuit?"""
    out = []
    by = collections.defaultdict(list)
    for r in rows:
        by[(r['function'], r['platform'], r['flow'])].append(r)
    for (fn, p, f), rs in sorted(by.items()):
        for m in MEASURES:
            best = min(rs, key=lambda r: r[m])
            bb = min((r for r in rs if r['part'] == 'baseline'), key=lambda r: r[m])
            out.append({'function': fn, 'platform': p, 'flow': f, 'measure': m,
                        'best': best['circuit'], 'best_key': best['key'], 'best_value': best[m],
                        'best_part': best['part'], 'best_baseline': bb['circuit'],
                        'best_baseline_key': bb['key'], 'best_baseline_value': bb[m],
                        'gain_vs_baseline': (bb[m] - best[m]) / bb[m]})
    return out


def inversion_shares(rows, thr):
    """Pooled over functions, per library, flow and measure: among dominated pairs whose physical
    difference is beyond noise, the share where the dominated (logically worse) circuit is
    physically better; and how often the file score (f_sta / f_area / f_pwr of the library) also
    puts the worse circuit first in those pairs.  For all circuits and for G < 400 only."""
    out = {}
    by = collections.defaultdict(list)
    for r in rows:
        by[(r['function'], r['platform'], r['flow'])].append(r)
    score = {'delay': 'f_sta_', 'area': 'f_area_', 'power': 'f_pwr_'}
    for subset in ('all', 'G<400'):
        acc = collections.defaultdict(lambda: [0, 0, 0])      # inverted, not inverted, score agrees
        for (fn, p, f), rs in by.items():
            if subset != 'all':
                rs = [r for r in rs if key4(r)[2] < 400]
            for m in ('delay', 'area', 'power'):
                t = thr(p, f, m)
                if t is None:
                    continue
                a = acc[(p, f, m)]
                for x, y in itertools.permutations(rs, 2):
                    if not dominates(key4(x), key4(y)):
                        continue                  # x logically better than y
                    if (x[m] - y[m]) / x[m] > t:
                        a[0] += 1
                        a[2] += y[score[m] + p] < x[score[m] + p]
                    elif (y[m] - x[m]) / y[m] > t:
                        a[1] += 1
        for (p, f, m), (inv, ok, agree) in acc.items():
            out['%s|%s|%s|%s' % (subset, p, f, m)] = {
                'beyond_noise_pairs': inv + ok, 'inverted': inv,
                'share': inv / (inv + ok) if inv + ok else None,
                'score_agrees': agree / inv if inv else None}
    return out


# ---- synthesis -------------------------------------------------------------------------------

def synthesis(rows):
    out = {}
    idx = {(r['circuit'], r['platform'], r['flow']): r for r in rows}
    circuits = collections.defaultdict(set)
    for r in rows:
        circuits[(r['function'], r['key'])].add(r['circuit'])
    for p in ('nangate45', 'sky130hd'):
        for f in ('preserve', 'free', 'free-area'):
            same = total = 0
            for (fn, k), cs in circuits.items():
                cs = [c for c in cs if (c, p, f) in idx]
                for a, b in itertools.combinations(cs, 2):
                    total += 1
                    same += idx[(a, p, f)]['m_hash'] == idx[(b, p, f)]['m_hash']
            out['identical_netlists|%s|%s' % (p, f)] = {'same_metric_pairs': total, 'identical': same}
    # rank agreement between configurations, per function and measure
    agree = {}
    for fn in FUNCS:
        cs = sorted({r['circuit'] for r in rows if r['function'] == fn})
        for m in MEASURES:
            mat = {}
            for c1, c2 in itertools.combinations(CONFIGS, 2):
                x = [idx[(c, *c1)][m] for c in cs if (c, *c1) in idx and (c, *c2) in idx]
                y = [idx[(c, *c2)][m] for c in cs if (c, *c1) in idx and (c, *c2) in idx]
                if len(x) > 5:
                    mat['%s/%s~%s/%s' % (*c1, *c2)] = float(stats.spearmanr(x, y)[0])
            agree['%s|%s' % (fn, m)] = mat
    # within same-metric groups: does the preserve ordering survive free synthesis?
    within = collections.defaultdict(list)
    for (fn, k), cs in circuits.items():
        cs = sorted(cs)
        if len(cs) < 4:
            continue
        for p in ('nangate45', 'sky130hd'):
            for f in ('free', 'free-area'):
                for m in ('delay', 'power', 'adp'):
                    x = [idx[(c, p, 'preserve')][m] for c in cs if (c, p, 'preserve') in idx and (c, p, f) in idx]
                    y = [idx[(c, p, f)][m] for c in cs if (c, p, 'preserve') in idx and (c, p, f) in idx]
                    if len(x) >= 4 and len(set(x)) > 1 and len(set(y)) > 1:
                        within['%s|preserve~%s|%s' % (p, f, m)].append(float(stats.spearmanr(x, y)[0]))
    win = {k: {'groups': len(v), 'mean_rho': float(np.mean(v)), 'median_rho': float(np.median(v))}
           for k, v in within.items()}
    return out, agree, win


# ---- prediction ------------------------------------------------------------------------------

FEATS = ['f_A', 'f_AD', 'f_G', 'f_GD', 'f_XOR', 'f_XNOR', 'f_NOT', 'f_fo_mean', 'f_fo_max',
         'f_fo_sd', 'f_fo_ge3', 'f_fo_ge5', 'f_fo_sumsq', 'f_in_fo_sum', 'f_in_fo_max',
         'f_out_depth_mean', 'f_out_depth_sd', 'f_out_at_max', 'f_zero_slack', 'f_slack_mean',
         'f_imbalance_mean', 'f_shared_frac', 'f_reconv_frac', 'f_overlap_mean']


def lib_feats(p):
    return ['f_sta_%s' % p, 'f_sta_crit_%s' % p, 'f_area_%s' % p, 'f_pwr_%s' % p]


ISO_KEYS = set()


def is_test(r):
    # every circuit of a same-metric (iso) key is on the side of its key (the group is held out
    # whole, baseline and spread members included); other circuits by their own hash
    tag = r['function'] + r['key'] if (r['function'], r['key']) in ISO_KEYS else r['circuit']
    return int(hashlib.sha1(tag.encode()).hexdigest(), 16) % 2 == 1


def proxies(r, p, m):
    """Abstract proxy and zero-fit physical proxy for measure m (lower is better)."""
    G, GD = r['f_G'], r['f_GD']
    abstract = {'area': G, 'delay': GD + 1e-3 * G, 'power': G, 'adp': G * GD}[m]
    sta, area, pwr = r['f_sta_' + p], r['f_area_' + p], r['f_pwr_' + p]
    physical = {'area': area, 'delay': sta, 'power': pwr, 'adp': area * sta}[m]
    return abstract, physical


def ridge_fit(X, y, lam=1.0):
    mu, sd = X.mean(0), X.std(0) + 1e-9
    Xs = (X - mu) / sd
    A = Xs.T @ Xs + lam * np.eye(X.shape[1])
    w = np.linalg.solve(A, Xs.T @ (y - y.mean()))
    return lambda Z: ((Z - mu) / sd) @ w + y.mean()


def rank_quality(pred, true, groups=None, thr=None):
    out = {'spearman': float(stats.spearmanr(pred, true)[0])
           if len(set(true)) > 1 and len(set(pred)) > 1 else 0.0}
    if groups is not None:
        rhos, ok, tot = [], 0, 0
        g = collections.defaultdict(list)
        for i, k in enumerate(groups):
            if k is not None:
                g[k].append(i)
        for k, ii in g.items():
            if len(ii) < 4:
                continue
            pt = [pred[i] for i in ii]
            tt = [true[i] for i in ii]
            if len(set(tt)) > 1:
                rhos.append(float(stats.spearmanr(pt, tt)[0]) if len(set(pt)) > 1 else 0.0)
            for a, b in itertools.combinations(ii, 2):
                if thr is not None and abs(true[a] - true[b]) / max(true[a], true[b]) > thr:
                    tot += 1
                    sgn = (pred[a] - pred[b]) * (true[a] - true[b])
                    ok += 1.0 if sgn > 0 else 0.5 if pred[a] == pred[b] else 0.0
        out['within_group_rho'] = float(np.mean(rhos)) if rhos else None
        out['within_groups'] = len(rhos)
        out['pair_accuracy_beyond_noise'] = ok / tot if tot else None
        out['pairs_beyond_noise'] = tot
    return out


def predict(rows, thr):
    res = {}
    idx = collections.defaultdict(list)
    for r in rows:
        idx[(r['platform'], r['flow'])].append(r)
    for (p, f), rs in idx.items():
        feats = FEATS + lib_feats(p)
        for m in MEASURES:
            t = thr(p, f, m)
            for fn in FUNCS:
                fr = [r for r in rs if r['function'] == fn]
                tr = [r for r in fr if not is_test(r)]
                te = [r for r in fr if is_test(r)]
                if len(tr) < 20 or len(te) < 10:
                    continue
                y_te = [r[m] for r in te]
                grp = [r['key'] for r in te]
                ab = [proxies(r, p, m)[0] for r in te]
                ph = [proxies(r, p, m)[1] for r in te]
                X = np.array([[r[k] for k in feats] for r in tr])
                y = np.log(np.array([r[m] for r in tr]))
                model = ridge_fit(X, y, lam=3.0)
                rg = list(model(np.array([[r[k] for k in feats] for r in te])))
                res['%s|%s|%s|%s' % (p, f, m, fn)] = {
                    'train': len(tr), 'test': len(te),
                    'abstract': rank_quality(ab, y_te, grp, t),
                    'physical_zero_fit': rank_quality(ph, y_te, grp, t),
                    'ridge': rank_quality(rg, y_te, grp, t)}
            # leave one function out (targets standardised within each function)
            for fn in FUNCS:
                tr = [r for r in rs if r['function'] != fn]
                te = [r for r in rs if r['function'] == fn]
                if not te:
                    continue

                def zs(sub):
                    out = {}
                    for g in FUNCS:
                        v = np.log([r[m] for r in sub if r['function'] == g])
                        if len(v):
                            out[g] = (v.mean(), v.std() + 1e-9)
                    return out
                ztr = zs(tr)

                def fz(sub):
                    X = []
                    for g in FUNCS:
                        part = [r for r in sub if r['function'] == g]
                        if not part:
                            continue
                        A = np.array([[r[k] for k in feats] for r in part], dtype=float)
                        A = (A - A.mean(0)) / (A.std(0) + 1e-9)
                        X.append(A)
                    return np.vstack(X)
                Xtr = fz(tr)
                ytr = np.concatenate([(np.log([r[m] for r in tr if r['function'] == g]) - ztr[g][0]) / ztr[g][1]
                                      for g in FUNCS if g in ztr])
                model = ridge_fit(Xtr, ytr, lam=3.0)
                pred = list(model(fz(te)))
                y_te = [r[m] for r in te]
                res['lofo|%s|%s|%s|%s' % (p, f, m, fn)] = {
                    'ridge': rank_quality(pred, y_te, [r['key'] for r in te], t),
                    'abstract': rank_quality([proxies(r, p, m)[0] for r in te], y_te,
                                             [r['key'] for r in te], t),
                    'physical_zero_fit': rank_quality([proxies(r, p, m)[1] for r in te], y_te,
                                                      [r['key'] for r in te], t)}
    return res


EXPLAIN = FEATS + ['f_sta', 'f_sta_crit', 'f_pwr', 'cells', 'm_depth', 'm_fo_max', 'm_xor',
                   'm_simple', 'm_complex', 'm_inv', 'm_buf', 'wire', 'delay_synth']


def explain(rows):
    """Which features track each measure *within* same-metric groups (where A, AD, G and GD
    cannot explain anything): mean Spearman over groups with >= 5 members, and the share of
    groups where the sign agrees with the mean.  File features come first; cells..delay_synth
    are measured after synthesis or routing (explanations, not search predictors)."""
    out = {}
    groups = collections.defaultdict(list)
    for r in rows:
        groups[(r['function'], r['key'], r['platform'], r['flow'])].append(r)
    for p, f in CONFIGS:
        for m in ('delay', 'power', 'area'):
            res = {}
            for feat in EXPLAIN:
                rhos = []
                for (fn, k, pp, ff), rs in groups.items():
                    if (pp, ff) != (p, f) or len(rs) < 5:
                        continue
                    col = feat + '_' + p if feat in ('f_sta', 'f_sta_crit', 'f_pwr') else feat
                    x = [r[col] for r in rs]
                    y = [r[m] for r in rs]
                    if len(set(x)) > 1 and len(set(y)) > 1:
                        rhos.append(float(stats.spearmanr(x, y)[0]))
                if len(rhos) >= 5:
                    mu = float(np.mean(rhos))
                    res[feat] = {'groups': len(rhos), 'mean_rho': mu,
                                 'sign_agree': float(np.mean([np.sign(x) == np.sign(mu) for x in rhos]))}
            out['%s|%s|%s' % (p, f, m)] = res
    return out


def screen(srows, rows, thr):
    """The prospective test: per pool, library, flow and measure, the score's top / random /
    bottom picks; one-sided Mann-Whitney p-values (top lower than random, top lower than
    bottom), and how the picks compare with the benchmark's circuits of the same metrics."""
    out = []
    pools = collections.defaultdict(list)
    for r in srows:
        pools[(r['function'], r['key'], r['platform'], r['flow'])].append(r)
    base = collections.defaultdict(list)
    for r in rows:
        if r['part'] == 'baseline':
            base[(r['function'], r['key'], r['platform'], r['flow'])].append(r)
    for (fn, k, p, f), rs in sorted(pools.items()):
        for m in MEASURES:
            g = {t: [r[m] for r in rs if r['part'] == 'screen-' + t] for t in ('top', 'random', 'bottom')}
            if min(len(v) for v in g.values()) < 5:
                continue
            p_tr = float(stats.mannwhitneyu(g['top'], g['random'], alternative='less').pvalue)
            p_tb = float(stats.mannwhitneyu(g['top'], g['bottom'], alternative='less').pvalue)
            rnd = [r for r in rs if r['part'] == 'screen-random']
            sc = [float(r['f_sta_' + p]) for r in rnd]
            rho = float(stats.spearmanr(sc, [r[m] for r in rnd])[0]) if len(set(sc)) > 1 else 0.0
            b = base.get((fn, k, p, f), [])
            out.append({'function': fn, 'key': k, 'platform': p, 'flow': f, 'measure': m,
                        'median': {t: float(np.median(v)) for t, v in g.items()},
                        'top_vs_random_median_change': float(np.median(g['top']) / np.median(g['random']) - 1),
                        'p_top_lt_random': p_tr, 'p_top_lt_bottom': p_tb,
                        'spearman_own_lib_score_on_random': rho,
                        'best_top': float(min(g['top'])), 'best_random': float(min(g['random'])),
                        'baseline_same_key': {r['circuit']: r[m] for r in b},
                        'threshold': thr(p, f, m)})
    # Holm-Bonferroni over every top-vs-random test
    order = sorted(range(len(out)), key=lambda i: out[i]['p_top_lt_random'])
    k = len(out)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (k - rank) * out[i]['p_top_lt_random']))
        out[i]['p_top_lt_random_holm'] = running
    return out


def main():
    rows, seeds = load()
    dups = [r for r in rows if r.get('dup_of')]
    rows = [r for r in rows if not r.get('dup_of')]
    ISO_KEYS.update((r['function'], r['key']) for r in rows if r['part'] == 'iso')
    srows = [r for r in rows if r['part'].startswith('screen')]
    rows = [r for r in rows if not r['part'].startswith('screen')]
    nsum, thr, per = noise(rows, seeds)
    isum, idetail = iso(rows, thr)
    vsum, vtop = inversions(rows, thr)
    bvp = best_vs_published(rows)
    same, agree, within = synthesis(rows)
    pred = predict(rows, thr)
    scr = screen(srows, rows, thr) if srows else []
    expl = explain(rows)
    ishare = inversion_shares(rows, thr)
    out = {'rows': len(rows), 'circuits': len({r['circuit'] for r in rows}), 'Z': Z,
           'duplicates_left_out': sorted({(r['circuit'], r['dup_of']) for r in dups}),
           'noise': nsum, 'iso': isum, 'iso_detail': idetail, 'inversions': vsum,
           'inversions_top': vtop, 'best_vs_published': bvp, 'synthesis_identical': same,
           'rank_agreement': agree, 'within_group_agreement': within, 'predict': pred,
           'screen': scr, 'explain': expl, 'inversion_shares': ishare,
           'seeded': {'%s|%s|%s|%s|%s' % k: v for k, v in per.items()}}
    (RES / 'analysis.json').write_text(json.dumps(out, indent=1, sort_keys=True, default=str) + '\n')
    print('wrote', RES / 'analysis.json', len(rows), 'rows', len(srows), 'screen rows')


if __name__ == '__main__':
    main()
