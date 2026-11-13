"""Consistency audit of the benchmark run files (bench.py output) in v1/ and v2/.

For every run: error / verified; final metrics vs the best feasible trajectory point (a final
better than the trajectory = the trajectory missed an improvement; a trajectory point better than
the final = an over-claim); trajectory times monotone and within the budget; XORFlux records order.
    python3 audit_bench.py
"""
import json
from collections import Counter, defaultdict
from pathlib import Path

B = Path.home() / 'xs-campaigns/2026-11-13-boolflux/bench'
OBJ = {'cost': lambda m: m[1], 'cost,gd': lambda m: (m[1], m[4]), 'a,cost': lambda m: (m[3], m[1])}


def main():
    for v in ('v1', 'v2'):
        d = B / v
        if not d.exists(): continue
        runs = [json.loads(f.read_text()) for f in sorted(d.glob('*.json'))]
        c = Counter(); notes = defaultdict(list)
        for r in runs:
            run = r['run']; lab = run['label']; caps = run.get('caps') or {}
            c['runs'] += 1
            if r.get('error'): c['error'] += 1; notes['error'].append((lab, r['error'][:120])); continue
            c['verified'] += bool(r.get('verified'))
            tr = r['trajectory']
            feas = [row for row in tr if all(cp is None or {'GD': row[4], 'AD': row[5], 'A': row[3]}[k] <= cp for k, cp in caps.items())]
            key = OBJ[run.get('objective', 'cost')]
            ts = [row[0] for row in tr]
            if ts != sorted(ts): c['traj_time_not_monotone'] += 1; notes['nonmono'].append(lab)
            if ts and ts[-1] > run['seconds'] + 1.0: c['traj_beyond_budget+1s'] += 1; notes['late'].append((lab, ts[-1], run['seconds']))
            sw = r.get('search_wall_s')
            if sw and sw > run['seconds'] + 2: c['search_wall_over_budget+2s'] += 1; notes['wall'].append((lab, round(sw, 1), run['seconds']))
            f = r.get('final')
            if not f or not r.get('verified'): continue
            fr = [0, f['cost'], f['G'], f['A'], f['GD'], f['AD']]
            if not feas:
                c['final_but_no_feasible_traj'] += 1; notes['nofeas'].append(lab); continue
            bt = min(feas, key=key)
            if key(bt) < key(fr): c['traj_better_than_final(overclaim)'] += 1; notes['over'].append((lab, bt, f))
            elif key(bt) > key(fr): c['final_better_than_traj(missed)'] += 1; notes['missed'].append((lab, bt[1:], fr[1:]))
            if run['tool'] == 'xorflux':
                c['xorflux_runs'] += 1
                c['xorflux_startup_s>2'] += r['overhead'].get('xorflux_startup_s', 0) > 2
        print('==', v, dict(c))
        for k, lst in notes.items():
            print('  ', k, len(lst), lst[:6])
        # XORFlux startup and BoolFlux kernel start-up overhead in the linear table
        xs = [r['overhead'].get('xorflux_startup_s') for r in runs if r['run']['tool'] == 'xorflux' and r.get('overhead')]
        bs = [r['overhead'].get('kernel_startup_s') for r in runs if r['run']['label'].startswith('L-') and r['run']['tool'] == 'boolflux' and r.get('overhead')]
        if xs: print('   xorflux startup s: min %.2f max %.2f' % (min(xs), max(xs)))
        if bs: print('   boolflux kernel startup s (linear): min %.3f max %.3f' % (min(bs), max(bs)))


if __name__ == '__main__':
    main()
