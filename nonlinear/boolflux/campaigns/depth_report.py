"""Gate count at a gate-depth cap: published NIST AES S-box circuits against depth-campaign runs.

    python3 nonlinear/boolflux/campaigns/depth_report.py RUN_DIR [RUN_DIR ...]

For each cap d, the published best is the smallest G among NIST's forward AES S-box circuits
(nonlinear/nist/aes-sbox and old-2020) with GD <= d, any A and AD.  Each run directory named
gd<d>-from-<start> contributes its verified best (re-verified here with both verifiers and the
cap).
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE.parents[1]))
import cli   # noqa: E402

REPO = HERE.parents[2]


def published():
    out = []
    for f in (REPO / 'nonlinear' / 'nist' / 'aes-sbox').glob('*.circ.txt'):
        a, ad, g, gd = (int(x) for x in re.search(r'-a(\d+)-ad(\d+)-g(\d+)-gd(\d+)-', f.name).groups())
        out.append((g, gd, a, ad, f.name))
    for f in (REPO / 'nonlinear' / 'nist' / 'old-2020').glob('aes-sbox-fwd-*.slp'):
        g, a, gd, ad = (int(x) for x in re.search(r'-g(\d+)-a(\d+)-d(\d+)-ad(\d+)', f.name).groups())
        out.append((g, gd, a, ad, f.name))
    return out


def main():
    pub = published()
    best = {}
    for d in sys.argv[1:]:
        for sj in Path(d).glob('gd*-from-*/summary.json'):
            cap = int(re.match(r'gd(\d+)-', sj.parent.name).group(1))
            s = json.loads(sj.read_text())
            v = cli.verify_file(s['best']['file'], 'aes', 'nist', {'GD': cap, 'AD': None, 'A': None})
            if not (v['core_ok'] and v['independent_ok'] and v['library_ok']):
                print("rejected (caps not met or not verified):", sj.parent.name); continue
            m = v['metrics']
            if cap not in best or m['G'] < best[cap][0]['G']:
                best[cap] = (m, sj.parent, s)
    print('| GD cap | published best G (A, AD, GD, file) | ours G | ours A, AD, GD | counts | run |')
    print('|---|---|---|---|---|---|')
    for cap in sorted(best):
        p = min((x for x in pub if x[1] <= cap), default=None)
        m, run, s = best[cap]
        ps = '%d (A%d AD%d GD%d, %s)' % (p[0], p[2], p[3], p[1], p[4]) if p else 'none'
        mark = '**%d**' % m['G'] if p is None or m['G'] < p[0] else str(m['G'])
        print('| %d | %s | %s | A%d AD%d GD%d | %s | %s |' % (cap, ps, mark, m['A'], m['AD'], m['GD'],
              ' '.join('%s %d' % kv for kv in m['counts'].items()), run.name))


if __name__ == '__main__':
    main()
