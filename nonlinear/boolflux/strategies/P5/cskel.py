"""Driver for invskel.c (P5): spec JSON -> stdin of the C search, output -> JSON like invskel.py.

usage: python3 cskel.py SPEC --depth D --maxcost C [--na 5] [--prefix lev:L1:L2,...]
           [--shard i/n] [--bin PATH] --out OUT.json
"""
import argparse, json, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('spec'); ap.add_argument('--depth', type=int, required=True)
    ap.add_argument('--maxcost', type=int, required=True); ap.add_argument('--na', type=int, default=5)
    ap.add_argument('--prefix', default=''); ap.add_argument('--shard', default='0/1')
    ap.add_argument('--bin', default=str(HERE / 'invskel_c')); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    s = json.load(open(a.spec))
    assert s['k'] == 4
    si, sn = a.shard.split('/')
    lines = ['%d %d %d %s %s' % (a.depth, a.na, a.maxcost, si, sn)]
    lines.append('%d ' % len(s['inputs']) + ' '.join('%s %d' % (i['table'][2:], 1 if i.get('paid') else 0) for i in s['inputs']))
    lines.append('%d ' % len(s['targets']) + ' '.join(t['table'][2:] for t in s['targets']))
    b = s.get('boundary', [])
    lines.append('%d ' % len(b) + ' '.join(x['table'][2:] for x in b))
    pre = [p.split(':') for p in a.prefix.split(',') if p]
    lines.append('%d ' % len(pre) + ' '.join('%s %s %s' % tuple(p) for p in pre))
    t0 = time.time()
    p = subprocess.run([a.bin], input='\n'.join(lines) + '\n', capture_output=True, text=True)
    res = []
    for ln in p.stdout.splitlines():
        if ln.startswith('STATS'): print(ln); continue
        f = ln.split()
        cost, kind = int(f[0]), int(f[1])
        ands = [[int(x.split(':')[0]), x.split(':')[1], x.split(':')[2]] for x in f[2:]]
        res.append({'cost': cost, 'kind': ['exact', 'exact+1', 'lb+2'][kind], 'exact': kind < 2, 'ands': ands})
    res.sort(key=lambda r: (r['cost'], r['kind'] == 'lb+2'))
    json.dump(res, open(a.out, 'w'))
    from collections import Counter
    print('elapsed %.1fs kept %d' % (time.time() - t0, len(res)), sorted(Counter((r['cost'], r['kind']) for r in res).items()))
    for r in res[:10]: print(r['cost'], r['kind'], ' '.join('L%d:%s&%s' % tuple(x) for x in r['ands']))
    sys.stderr.write(p.stderr[-2000:])
    return p.returncode


if __name__ == '__main__':
    sys.exit(main())
