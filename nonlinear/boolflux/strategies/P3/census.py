"""Census of archive circuits within T04 hard limits (A<=32, AD<=4): per (A, GD) best G."""
import glob, json, os, collections, sys
H = os.path.expanduser('~/xs-campaigns/2026-11-14-hub')
GMAX = int(sys.argv[1]) if len(sys.argv) > 1 else 135
best = {}
cnt = collections.Counter()
for d in glob.glob(H + '/*/archive'):
    for f in glob.glob(d + '/*.json'):
        try:
            r = json.load(open(f))
        except Exception:
            continue
        if not isinstance(r, dict) or 'A' not in r:
            continue
        if r['A'] <= 32 and r['AD'] <= 4:
            k = (r['A'], r['GD'])
            cnt[k] += 1
            if k not in best or r['G'] < best[k][0]:
                best[k] = (r['G'], f[:-5] + '.bfx')
for k in sorted(best):
    if best[k][0] <= GMAX:
        print(k, best[k][0], cnt[k], best[k][1])
