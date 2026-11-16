"""Compare frontier-campaign results with every published NIST circuit of the same function.

    python3 search/nonlinear/campaigns/frontier_report.py OUTDIR aes-sbox [--copy DEST]

For each start circuit: its metrics (A, AD, G, GD), the best result found under its own caps,
and whether that result is new on NIST's published set, i.e. no published circuit has
A, AD, G and GD all <= the result's (the result is not dominated or equalled).  With --copy,
every improved circuit is copied to DEST under a NIST-style name.
"""
import json
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PAT = re.compile(r'-a(\d+)-ad(\d+)-g(\d+)-gd(\d+)-')


def published(d):
    out = []
    for f in sorted((REPO / 'search' / 'nonlinear' / 'seeds' / d).glob('*.circ.txt')):
        m = PAT.search(f.name)
        out.append((f.name, tuple(int(x) for x in m.groups())))
    return out


def dominated(p, pub):
    """published circuits with every metric <= p (A, AD, G, GD)."""
    return [n for n, q in pub if all(a <= b for a, b in zip(q, p))]


def main():
    out = Path(sys.argv[1]); d = sys.argv[2]
    dest = Path(sys.argv[sys.argv.index('--copy') + 1]) if '--copy' in sys.argv else None
    pub = published(d)
    rows = []
    for name, p0 in pub:
        sj = out / name.replace('.circ.txt', '') / 'summary.json'
        if not sj.exists():
            continue
        s = json.loads(sj.read_text())
        b = s['best']; m = b['metrics']
        p = (m['A'], m['AD'], m['G'], m['GD'])
        ok = b['core_ok'] and b['independent_ok'] and b['library_ok']
        dom = dominated(p, pub)
        new = ok and not dom
        improved = ok and p != p0 and all(a <= c for a, c in zip(p, p0))
        rows.append((name, p0, p, ok, improved, new, dom))
        if dest and improved:
            dest.mkdir(parents=True, exist_ok=True)
            nm = 'boolflux-%s-a%d-ad%d-g%d-gd%d-from-%s' % ((d,) + p + (name,))
            shutil.copy(b['file'], dest / nm)
    print('| start (NIST) | A AD G GD | best found | verified | dominates start | not dominated by any published |')
    print('|---|---|---|---|---|---|')
    for name, p0, p, ok, imp, new, dom in rows:
        print('| %s | %s | %s | %s | %s | %s |' % (name.replace('.circ.txt', ''), ' '.join(map(str, p0)),
              ' '.join(map(str, p)), 'yes' if ok else 'NO', 'yes' if imp else '', 'NEW' if new else ''))
    print()
    print('%d starts, %d improved, %d new on the published set' % (
        len(rows), sum(r[4] for r in rows), sum(r[5] for r in rows)))


if __name__ == '__main__':
    main()
