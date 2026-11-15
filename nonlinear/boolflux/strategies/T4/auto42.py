#!/usr/bin/env python3
"""T4 driver: turn a search42.py solution into a verified circuit.
For the basis outputs: 'p2' with PAIR; for every other output with saving > 0: explicit designs
from cxplan.py (2- or 3-product).  Build (build46), polarity pass, skeleton bound; outputs above the
cap try their alternative designs, then fall back to rank-1 ('r1').  A bound-11 skeleton is
synthesised (depthsynth) and checked with aes_check; result JSON on stdout.
    python3 auto42.py FRONT SOLUTION_JSON OUTDIR [CAP]"""
import sys, json, os, subprocess, itertools
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import build46 as B46  # noqa
import polpass as PP  # noqa
import depthsynth as DS  # noqa
from coversearch import bound  # noqa
from boolflux import core, targets, skeleton  # noqa

MODEL = core.Model.load('nist')
SBOX = tuple(targets.aes_sbox())


def cx_variants(front, k, basis, pair, maxn=8):
    env = dict(os.environ, T4_BASIS=','.join(map(str, basis)), T4_PAIR=pair, T4_PERDESIGN='2')
    r = subprocess.run([sys.executable, str(HERE / 'cxplan.py'), front, str(k), str(maxn)], capture_output=True, text=True, env=env, timeout=900)
    out = []
    for ln in r.stdout.splitlines():
        if ln.startswith('%d:cx' % k): out.append(ln.split(':', 1)[1])
    return out


def nprod(plan):
    if plan == 'r1': return 4
    return len(plan.split('|'))


def try_build(front, plans, order):
    os.environ['T4_ORDER'] = ','.join(map(str, order))
    sk, ok = B46.build(front, plans)
    if not ok: return None
    sk2 = PP.polarity_pass(sk)
    tab, ft, ones = skeleton._form_tables(sk2)
    St = core.tables_from_values(8, 8, targets.aes_sbox())
    for k in range(8):
        if ft(sk2['outputs'][k]) ^ St[k] == ones: sk2['outputs'][k] ^= 1
    if not all(ft(sk2['outputs'][k]) == St[k] for k in range(8)): return None
    b, arr, ol = bound(sk2, 8)
    return sk2, b, ol, len(sk2['ands'])


if __name__ == '__main__':
    front, sol, outdir = sys.argv[1], json.loads(sys.argv[2]), Path(sys.argv[3])
    cap = int(sys.argv[4]) if len(sys.argv) > 4 else 11
    outdir.mkdir(parents=True, exist_ok=True)
    basis = sol['B']; pair = sol.get('pair', '02-13')
    pr = [tuple(int(ch) for ch in p) for p in pair.split('-')]
    p2 = 'p2 %d %d %d %d' % (pr[0][0], pr[0][1], pr[1][0], pr[1][1])
    plans = {k: p2 for k in basis}
    alts = {}
    for ks, (sv, ex) in sol['detail'].items():
        k = int(ks)
        if k in basis or sv <= 0: continue
        vs = [v for v in cx_variants(front, k, basis, pair) if nprod(v) == 4 - sv]
        if vs: alts[k] = vs; plans[k] = vs[0]
    order = list(basis) + [k for k in range(8) if k not in basis]
    res = try_build(front, plans, order)
    log = []
    for rnd in range(3):
        if res is None: break
        sk, b, ol, nA = res
        log.append({'round': rnd, 'ANDs': nA, 'bound': b, 'outs': ol})
        bad = [k for k in range(8) if ol[k] > cap]
        if not bad: break
        for k in bad:
            if k in basis or k not in plans: continue
            improved = False
            for v in alts.get(k, [])[1:]:
                p = dict(plans); p[k] = v
                r2 = try_build(front, p, order)
                if r2 and r2[2][k] <= cap and max(r2[2]) <= max(res[2]):
                    plans, res, improved = p, r2, True; break
            if not improved:
                p = dict(plans); p.pop(k)
                r2 = try_build(front, p, order)
                if r2: plans, res = p, r2
    rec = {'solution': sol, 'plans': plans, 'log': log}
    if res is not None:
        sk, b, ol, nA = res
        rec.update({'ANDs': nA, 'bound': b})
        if b <= cap:
            c = DS.synth(sk)
            assert tuple(c.value_table()) == SBOX
            m = c.metrics(MODEL)
            f = outdir / ('auto-a%d-gd%d.circ.txt' % (m['A'], m['GD']))
            f.write_text(core.write_ncff(c, MODEL, comments=['T4 auto42 plans %s' % plans]))
            (outdir / ('auto-a%d-gd%d.skel.json' % (m['A'], m['GD']))).write_text(json.dumps(
                {'plans': {str(k): v for k, v in plans.items()}, 'ands': [[hex(L), hex(R)] for L, R in sk['ands']], 'outputs': [hex(F) for F in sk['outputs']]}))
            rec['circuit'] = str(f); rec['metrics'] = [m['A'], m['AD'], m['G'], m['GD']]
    print(json.dumps(rec, default=str), flush=True)
