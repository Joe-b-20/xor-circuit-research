"""Pooled, paired comparisons over rounds (same map/cap/start/seed/round = same CPU, back to back).

    python3 nonlinear/boolflux/bench/pooled.py RUNDIR [RUNDIR ...]

Linear maps: XORFlux v8 vs XOR-only BoolFlux, paired by (round dir, seed): wins/ties/losses on the
final verified G (then depth), medians, and a two-sided sign test p-value.  AES a36 warm start:
BoolFlux with and without the no-op filter (skip_noop 0 = v1, 1 = v2), unpaired.
"""
import json
import math
import re
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path


def sign_p(w, l):
    n = w + l
    if n == 0: return 1.0
    k = min(w, l)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):      # review5 P16
        print(__doc__.strip()); sys.exit(0 if len(sys.argv) > 1 and sys.argv[1] in ('-h', '--help') else 2)
    pairs = defaultdict(dict); a36 = defaultdict(list)
    for d in sys.argv[1:]:
        for f in Path(d).glob('*.json'):
            r = json.loads(f.read_text()); lab = r['run']['label']
            m = re.match(r'^L-(.+)-c(4|none)-(naive|nist)-s(\d+)-(xorflux|boolflux-v\d+)$', lab)
            if m and r.get('verified'):
                key = (m.group(1), m.group(2), m.group(3)); tool = 'X' if m.group(5) == 'xorflux' else 'B'
                pairs[key].setdefault((d, int(m.group(4))), {})[tool] = (r['final']['G'], r['final']['GD'])
            m = re.match(r'^A-aes-a36g142-gate-s(\d+)-(v\d)$', lab)
            if m:
                a36[r['run']['set'].get('skip_noop', 1)].append(r['final']['G'] if r.get('verified') else None)
    print('| map | cap | start | pairs | BoolFlux better / equal / XORFlux better (G, then GD) | sign-test p | median G BoolFlux | median G XORFlux |')
    print('|---|---|---|---|---|---|---|---|')
    for key in sorted(pairs):
        ps = [v for v in pairs[key].values() if 'X' in v and 'B' in v]
        w = sum(1 for v in ps if v['B'] < v['X']); l = sum(1 for v in ps if v['B'] > v['X']); t = len(ps) - w - l
        print('| %s | %s | %s | %d | %d / %d / %d | %.3f | %s | %s |' % (key[0], key[1], key[2], len(ps), w, t, l, sign_p(w, l),
              st.median(v['B'][0] for v in ps), st.median(v['X'][0] for v in ps)))
    print()
    for k in sorted(a36):
        g = [x for x in a36[k] if x is not None]
        print('AES a36-ad4-g142-gd13, gate config, skip_noop %d: %d runs, median G %s, <=132 in %d, <=133 in %d'
              % (k, len(g), st.median(g) if g else '-', sum(1 for x in g if x <= 132), sum(1 for x in g if x <= 133)))


if __name__ == '__main__':
    main()
