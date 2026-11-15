#!/usr/bin/env python3
"""T4 pipeline: stage-1 cover swap (coincov candidate) -> skeleton bound -> rank-2 bottom plans with
shared junk (build46) -> depth-optimal synthesis -> verification.
    python3 pipe43.py FRONT_CIRCUIT HITS.jsonl SCORES.txt OUTDIR [MAXCAND]
SCORES.txt = coinscore.py output (JSON lines with class, g, choice)."""
import sys, json, os
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from rank2 import load, analyse, ONES  # noqa
import coversearch as CS  # noqa
import build46 as B46  # noqa
import depthsynth as DS  # noqa
from boolflux import core, skeleton, targets  # noqa

MODEL = core.Model.load('nist')
SBOX = tuple(targets.aes_sbox())


def plan_str(choice):
    out = {}
    for k, d in choice:
        if d[0] == 'p3': out[k] = 'p3 %d %d' % tuple(d[1])
        else: out[k] = 'p2 %d %d %d %d' % (d[1][0][0], d[1][0][1], d[1][1][0], d[1][1][1])
    return out


def run(front, keys, choice, outdir, tag):
    c = load(front); n = c.n
    T, lg, la, fa, ba, V, X0 = analyse(c)
    sk = skeleton.extract(c)
    ands_sig = [n + j for j, g in enumerate(c.gates) if g[0] in core.NONLINEAR_OPS]
    lvl1 = [k for k, s in enumerate(ands_sig) if la[s] == 1]
    oldA1tab = [T[ands_sig[k]] for k in lvl1]
    X = core.input_tables(8)
    sc, sk1, ch = CS.optimise(sk, n, lvl1, oldA1tab, keys, X, passes=3)
    rec = {'tag': tag, 'cover_bound': sc[0]}
    if sk1 is None or sc[0] > 11:
        return rec
    c1 = DS.synth(sk1)
    assert tuple(c1.value_table()) == SBOX
    f1 = outdir / ('c1-%s.circ.txt' % tag)
    f1.write_text(core.write_ncff(c1, MODEL, comments=['T4 pipe43 cover swap %s' % tag]))
    m1 = c1.metrics(MODEL); rec['c1'] = [m1['A'], m1['AD'], m1['G'], m1['GD']]
    plans = plan_str(choice)
    rec['plans'] = plans
    # try the full plan, then drop outputs one at a time if depth fails
    best = None
    tried = [plans]
    for k in list(plans):
        p = dict(plans); p.pop(k); tried.append(p)
    for p in tried:
        try:
            sk2, ok = B46.build(str(f1), p)
        except Exception as e:
            continue
        if not ok: continue
        b, arr, ol = CS.bound(sk2, 8)
        cand = (b > 11, len(sk2['ands']), b, p, sk2)
        if best is None or cand[:2] < best[:2]: best = cand
    if best is None:
        rec['build'] = 'failed'; return rec
    _, nA, b, p, sk2 = best
    rec.update({'best_plans': p, 'ANDs': nA, 'bound': b})
    if b <= 12:
        c2 = DS.synth(sk2)
        assert tuple(c2.value_table()) == SBOX
        m2 = c2.metrics(MODEL); rec['c2'] = [m2['A'], m2['AD'], m2['G'], m2['GD']]
        f2 = outdir / ('c2-%s-a%d-gd%d.circ.txt' % (tag, m2['A'], m2['GD']))
        f2.write_text(core.write_ncff(c2, MODEL, comments=['T4 pipe43 %s plans %s' % (tag, p)]))
        (outdir / ('c2-%s-a%d-gd%d.skel.json' % (tag, m2['A'], m2['GD']))).write_text(json.dumps(
            {'plans': p, 'ands': [[hex(L), hex(R)] for L, R in sk2['ands']], 'outputs': [hex(F) for F in sk2['outputs']]}))
        rec['file'] = str(f2)
    return rec


if __name__ == '__main__':
    front, hitsf, scoref, outdir = sys.argv[1], sys.argv[2], sys.argv[3], Path(sys.argv[4])
    maxc = int(sys.argv[5]) if len(sys.argv) > 5 else 10
    outdir.mkdir(parents=True, exist_ok=True)
    keysof = {}
    for ln in open(hitsf):
        r = json.loads(ln); keysof[(r['class'], tuple(r['g']))] = [frozenset(k) for k in r['keys']]
    cands = [json.loads(l) for l in open(scoref) if l.startswith('{')]
    for i, cnd in enumerate(cands[:maxc]):
        key = (cnd['class'], tuple(cnd['g']))
        tag = 'c%d-g%d-%d' % (key[0], key[1][0], key[1][1])
        try:
            rec = run(front, keysof[key], cnd['choice'], outdir, tag)
        except Exception as e:
            rec = {'tag': tag, 'error': repr(e)[:200]}
        rec['net_expected'] = cnd['net']
        print(json.dumps(rec), flush=True)
