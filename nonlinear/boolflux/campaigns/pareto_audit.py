"""AES S-box results against the pinned NIST baseline, on (A, AD, G, GD), lower is better.

    python3 nonlinear/boolflux/campaigns/pareto_audit.py [--json OUT.json]

Published set: every forward AES S-box circuit in nonlinear/nist/ (aes-sbox/, old-2020/
aes-sbox-fwd-*, sbox/aes-sbox-fwd-*), metrics computed from the files by the independent
verifier (G counts NOT; A counts every nonlinear gate; GD counts every gate as a level).
Results: nonlinear/boolflux/results/aes/*.circ.txt, metrics from the independent verifier and
from core, which must agree.  A result survives when no published circuit has all four metrics
<= its own and no other result strictly dominates it; results with identical tuples are
reported once.  Also the smallest G at each gate-depth cap.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
REPO = PKG.parents[1]
sys.path.insert(0, str(PKG / 'independent'))
sys.path.insert(0, str(PKG.parent))
import verify as V                       # noqa: E402  (independent verifier)
from boolflux import core, targets       # noqa: E402

NIST = REPO / 'nonlinear' / 'nist'
BASIS = {'AND', 'XOR', 'XNOR', 'NOT'}


def ind_metrics(path):
    r = V.verify_file(str(path), (8, 8, V.aes_sbox()))
    if not r['ok']:
        raise SystemExit('independent verifier rejects %s: %s' % (path, r.get('errors') or r.get('mismatch')))
    m = r['metrics']
    return (m['A'], m['AD'], m['G'], m['GD']), m


def published():
    files = sorted(NIST.glob('aes-sbox/*.circ.txt')) + sorted(NIST.glob('old-2020/aes-sbox-fwd-*.slp')) \
        + sorted(NIST.glob('sbox/aes-sbox-fwd-*'))
    out = []
    for f in files:
        t, m = ind_metrics(f)
        out.append({'file': str(f.relative_to(REPO)), 'tuple': t})
    return out


def results():
    out = []
    tab = targets.aes_sbox()
    for f in sorted((PKG / 'results' / 'aes').glob('*.circ.txt')):
        t, m = ind_metrics(f)
        c = core.read_ncff(str(f))
        cm = c.metrics()
        assert c.value_table() == tab, f
        assert (cm['A'], cm['AD'], cm['G'], cm['GD']) == t, (f, cm, t)
        ops = set(m['counts'])
        s = json.loads(f.with_suffix('').with_suffix('.summary.json').read_text())
        out.append({'file': str(f.relative_to(REPO)), 'tuple': t, 'counts': m['counts'],
                    'basis_ok': ops <= BASIS | {'XNOR'}, 'start': s['start'], 'caps': s['caps']})
    return out


def le(p, q):
    return all(a <= b for a, b in zip(p, q))


def main():
    pub = published(); res = results()
    by_tuple = {}
    for r in res:
        by_tuple.setdefault(r['tuple'], []).append(r)
    rows = []
    for t, group in sorted(by_tuple.items(), key=lambda kv: (kv[0][3], kv[0][2])):
        dom_pub = [p['file'].split('/')[-1] for p in pub if le(p['tuple'], t)]
        eq_pub = [p['file'].split('/')[-1] for p in pub if p['tuple'] == t]
        dom_ours = [str(u) for u in by_tuple if u != t and le(u, t)]
        rows.append({'tuple': t, 'files': [g['file'] for g in group], 'basis_ok': all(g['basis_ok'] for g in group),
                     'dominated_by_published': dom_pub, 'equal_to_published': eq_pub,
                     'dominated_by_ours': dom_ours,
                     'survives': not dom_pub and not dom_ours})
    print('Published forward AES circuits: %d; result files: %d; distinct result tuples: %d\n'
          % (len(pub), len(res), len(by_tuple)))
    print('| A AD G GD | files | survives | published circuits with all four <= | our tuples that dominate |')
    print('|---|---|---|---|---|')
    for r in rows:
        print('| %s | %d | %s | %s | %s |' % (' '.join(map(str, r['tuple'])), len(r['files']),
              '**yes**' if r['survives'] else 'no', ', '.join(x.replace('.circ.txt', '') for x in r['dominated_by_published'][:3])
              + (' (+%d)' % (len(r['dominated_by_published']) - 3) if len(r['dominated_by_published']) > 3 else ''),
              ', '.join(r['dominated_by_ours'][:3])))
    print('\n%d surviving tuples\n' % sum(r['survives'] for r in rows))
    print('| GD <= | published best G (A AD G GD) | ours best G (A AD G GD) |')
    print('|---|---|---|')
    caps = []
    for d in range(9, 41):
        p = min((x['tuple'] for x in pub if x['tuple'][3] <= d), key=lambda t: (t[2], t), default=None)
        o = min((x['tuple'] for x in res if x['tuple'][3] <= d), key=lambda t: (t[2], t), default=None)
        if o and (not p or o[2] < p[2]):
            caps.append(d)
            print('| %d | %s | **%s** |' % (d, ' '.join(map(str, p)) if p else 'none', ' '.join(map(str, o))))
    print('\nstrictly better G at GD caps: %s' % (caps or 'none'))
    if '--json' in sys.argv:
        Path(sys.argv[sys.argv.index('--json') + 1]).write_text(json.dumps(
            {'published': pub, 'rows': rows, 'strict_caps': caps}, indent=1) + '\n')


if __name__ == '__main__':
    main()
