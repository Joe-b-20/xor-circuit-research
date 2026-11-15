"""P5: for skeletons found with all 15 linear forms of the inversion inputs free (inv103all_*),
find which 4-form bases B make the skeleton cost the same with only B free (other linear forms
then cost gates).  For each skeleton: O = pure-linear AND operands; for every basis B containing
O (if O is independent and |O| <= 4), the exact cost is recomputed by the C search with the
skeleton as a full prefix and inputs = B.  Prints the distribution and the (skeleton, B) pairs
whose cost stays at the relaxed cost.

usage: python3 basisneed.py SKEL.json SPEC_ALL.json --depth D [--limit N] --out OUT.json
"""
import argparse, itertools, json, subprocess, sys
from collections import Counter
from pathlib import Path
HERE = Path(__file__).resolve().parent
LIN = {}
for m in range(1, 16):
    t = 0
    for x in range(16):
        b = 0
        for v in range(4):
            if m >> v & 1: b ^= (x >> v) & 1
        t |= b << x
    LIN[t] = m; LIN[t ^ 0xffff] = m


def rank(ms):
    rows = []
    for m in ms:
        for r in rows:
            if m ^ r < m: m ^= r
        if m: rows.append(m); rows.sort(reverse=True)
    return len(rows)


def cost(skel, B, spec, D):
    lines = ['%d 5 99 0 1' % D]
    tab = {m: t for t, m in LIN.items() if t < 0x8000 or True}
    ins = []
    for m in B:
        t = [tt for tt, mm in LIN.items() if mm == m and not (tt & 1)][0]   # the form with f(0) = 0
        ins.append('%04x 0' % t)
    lines.append('%d ' % len(ins) + ' '.join(ins))
    lines.append('%d ' % len(spec['targets']) + ' '.join(t['table'][2:] for t in spec['targets']))
    lines.append('0 ')
    lines.append('%d ' % len(skel['ands']) + ' '.join('%d %s %s' % (l, x, y) for l, x, y in skel['ands']))
    p = subprocess.run([str(HERE / 'invskel_c2')], input='\n'.join(lines) + '\n', capture_output=True, text=True)
    for ln in p.stdout.splitlines():
        if not ln.startswith('STATS'):
            f = ln.split(); return int(f[0]), int(f[1])
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('skel'); ap.add_argument('spec'); ap.add_argument('--depth', type=int, required=True)
    ap.add_argument('--limit', type=int, default=100000); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    sk = json.load(open(a.skel))[:a.limit]; spec = json.load(open(a.spec))
    osz = Counter(); res = []; dist = Counter()
    for i, s in enumerate(sk):
        O = sorted({LIN[int(x, 16)] for l, x, y in s['ands'] for x in (x, y) if int(x, 16) in LIN})
        osz[len(O)] += 1
        if len(O) > 4 or rank(O) < len(O): continue
        others = [m for m in range(1, 16) if m not in O]
        for ext in itertools.combinations(others, 4 - len(O)):
            B = O + list(ext)
            if rank(B) < 4: continue
            c, k = cost(s, B, spec, a.depth)
            dist[c] += 1
            if c is not None and c <= s['cost']:
                res.append({'rank': i, 'basis_masks': B, 'cost': c, 'kind': k, 'ands': s['ands']})
    print('|O| distribution', sorted(osz.items()))
    print('cost distribution over (skeleton, basis)', sorted((k, v) for k, v in dist.items() if k is not None)[:10])
    print('pairs at the relaxed cost', len(res))
    json.dump(res, open(a.out, 'w'))


if __name__ == '__main__':
    sys.exit(main())
