"""review3: consistency checks over the raw bench run JSONs.

    python3 check_bench_data.py ~/xs-campaigns/2026-11-13-boolflux/bench/{v1,v2,v3,v4}

For every run JSON (bench.py output) report:
  T1  final (verified) metrics better than the last feasible trajectory point (trajectory lost an improvement)
  T2  trajectory point better than final (best lost / final worse than logged)
  T3  trajectory not monotone in the run objective
  B1  search_wall_s exceeding the budget by more than 1 s / 5 %
  V   unverified / error runs
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from boolflux import cli  # noqa: E402


def objf(run):
    w = cli.objective_weights(run.get('objective', 'cost'))
    return lambda m: (w['w.cost'] * m['cost'] + w['w.g'] * m['G'] + w['w.a'] * m['A']
                      + w['w.gd'] * m['GD'] + w['w.ad'] * m['AD'])


def main():
    stats = Counter(); ex = defaultdict(list)
    for d in sys.argv[1:]:
        for f in sorted(Path(d).glob('*.json')):
            r = json.loads(f.read_text()); run = r['run']; lab = run['label'] + '@' + Path(d).name
            caps = run.get('caps') or {}
            feas = lambda m: all(c is None or m[k] <= c for k, c in caps.items())
            obj = objf(run)
            stats['runs'] += 1
            if r.get('error') or not r.get('verified'):
                stats['V'] += 1; ex['V'].append((lab, r.get('error'), r.get('final')))
            tr = [{'t': x[0], 'cost': x[1], 'G': x[2], 'A': x[3], 'GD': x[4], 'AD': x[5]} for x in r['trajectory']]
            ftr = [m for m in tr if feas(m)]
            if run['tool'] == 'boolflux' and len(tr) > 1:
                for a, b in zip(tr[1:], tr[2:]):
                    if obj(b) > obj(a) + 1e-12:
                        stats['T3'] += 1; ex['T3'].append((lab, a, b)); break
            if r.get('final') and r.get('verified') and ftr:
                fo, lo = obj(r['final']), obj(ftr[-1])
                if run['tool'] == 'xorflux':
                    fo, lo = (r['final']['G'], r['final']['GD']), (ftr[-1]['G'], ftr[-1]['GD'])
                if fo < lo:
                    stats['T1'] += 1; ex['T1'].append((lab, {k: r['final'][k] for k in ('G', 'A', 'GD', 'AD')},
                                                       {k: ftr[-1][k] for k in ('t', 'G', 'A', 'GD', 'AD')}))
                elif fo > lo:
                    stats['T2'] += 1; ex['T2'].append((lab, r['final'], ftr[-1]))
            if r.get('final') and r.get('verified') and not ftr:
                stats['T1nofeas'] += 1; ex['T1nofeas'].append((lab, r['final']))
            sw = r.get('search_wall_s')
            if sw is not None and sw > run['seconds'] + max(1.0, 0.05 * run['seconds']):
                stats['B1'] += 1; ex['B1'].append((lab, run['seconds'], round(sw, 2)))
    print(dict(stats))
    for k, v in ex.items():
        print('\n==', k, len(v))
        for e in v[:12]: print('  ', e)
    reach_vs_final(sys.argv[1:])


def reach_vs_final(dirs):
    """analyze.py's 'reach target' (from the trajectory) against the same predicate on the final
    verified circuit; prints every group where the two counts differ."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'bench'))
    import analyze
    print('\n== reach-target count: analyze.py (trajectory) vs final verified circuit')
    for d in dirs:
        runs = analyze.load([d]); groups = defaultdict(list)
        for r in runs:
            lab = r['run']['label']
            if lab[:2] not in ('N-', 'A-', 'X-', 'F-'): continue
            import re
            body = re.sub(r'-s\d+-v\d+$', '', lab[2:])
            names = sorted(list(analyze.NL) + ['aes'], key=len, reverse=True)
            tgt = next(t for t in names if body.startswith(t + '-'))
            groups[(lab[0], body, lab.rsplit('-', 1)[1])].append((tgt, r))
        for g, rs in sorted(groups.items()):
            tgt = rs[0][0]; key = tgt if tgt in analyze.NL else 'aes-a36g142'
            pred = analyze.NL[key][1]
            n_traj = sum(1 for _, r in rs if analyze.first_time(r, pred) is not None)
            caps = lambda r: r['run'].get('caps') or {}
            n_fin = sum(1 for _, r in rs if r.get('verified') and r.get('final') and pred(r['final'])
                        and all(c is None or r['final'][k] <= c for k, c in caps(r).items()))
            if n_traj != n_fin:
                print('  %s %s: analyze reach %d/%d, final meets target %d/%d'
                      % (Path(d).name, ' '.join(g), n_traj, len(rs), n_fin, len(rs)))


if __name__ == '__main__':
    main()
