#!/usr/bin/env python3
"""Run the package's own LP relaxation (lp_regen.py, unchanged, imported from the
package copy) at G=75 and G=76 and record which oriented claims survive, i.e. for
which steady-orbit profiles the local inequality system (L1)-(L23) cannot push the
two-step drift k+ell above the budget a+b+2G-192 (or k>S_e / ell>S_o).

Also records the scalar-domain sizes at G=73..77 for scaling, timing per LP, and
for each survivor the shortfall budget-(k+ell).
"""
import json, sys, time
from pathlib import Path

PKG = Path.home()/'xs-campaigns/2026-11-07-sprint/lb76/pkg_copy/source/lower_bounds/checks'
sys.path.insert(0, str(PKG))
import lp_regen  # noqa: E402  (the package's own LP model, unchanged)

OUT = Path.home()/'xs-campaigns/2026-11-07-sprint/lb76'

def main():
    Gs = [int(a) for a in sys.argv[1:]] or [75]
    report = {'scalar_states': {}, 'runs': {}}
    for G in range(73, 78):
        report['scalar_states'][G] = len(list(lp_regen.scalar_states(G)))
    print('scalar states by G:', report['scalar_states'], flush=True)
    for G in Gs:
        lp_regen.feasible.cache_clear(); lp_regen.UNKNOWN.clear()
        t0 = time.time()
        states, claims, survivors = lp_regen.run(G)
        dt = time.time()-t0
        keys = lp_regen.feasible.cache_info().currsize
        surv = []
        for st, ori, k, ell in survivors:
            a, b, Y, V, he, ho, le, lo, Se, So, budget = st
            surv.append({'state': list(st), 'orientation': ori, 'k': k, 'ell': ell,
                         'Se': Se, 'So': So, 'budget': budget, 'shortfall': budget-(k+ell),
                         'a': a, 'b': b, 'Y': Y, 'V': V, 'he': he, 'ho': ho})
        # how many distinct (h,y,F,q,z,ori) keys were LP-feasible (these are the local systems
        # a 76 proof would have to kill with new rows)
        feas_keys = [k for k, v in lp_regen.feasible.cache.items()] if hasattr(lp_regen.feasible, 'cache') else []
        report['runs'][G] = {'states': len(states), 'claims': len(claims), 'survivors': len(survivors),
                             'lp_keys': keys, 'seconds': round(dt, 1), 'unknown_lp': len(lp_regen.UNKNOWN),
                             'survivor_list': surv}
        print(f'G={G}: {len(survivors)} survivors of {len(claims)} claims; {keys} LP keys in {dt:.0f}s', flush=True)
        from collections import Counter
        print(' shortfall histogram:', sorted(Counter(s['shortfall'] for s in surv).items()), flush=True)
        print(' survivors by (a,b):', sorted(Counter((s['a'], s['b']) for s in surv).items()), flush=True)
        print(' survivors by (Y,V):', sorted(Counter((s['Y'], s['V']) for s in surv).items()), flush=True)
        print(' survivors by orientation:', sorted(Counter(s['orientation'] for s in surv).items()), flush=True)
        (OUT/f'g{G}_survivors.json').write_text(json.dumps(report['runs'][G], indent=1)+'\n')
    (OUT/'g75_scan_report.json').write_text(json.dumps(report, indent=1, default=str)+'\n')

if __name__ == '__main__':
    main()
