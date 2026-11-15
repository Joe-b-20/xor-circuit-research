#!/usr/bin/env python3
"""X1b: registry of known AND spaces (span{1, x, AND tables}, canonical hash; see x1b_family.py).

    python3 x1b_registry.py OUT.json [--amax 29] [--archive CAMPAIGN_DIR]... PATH...
PATH = files (.bfx / .circ.txt) or directories (all such files inside, not recursive).
Writes {span_hash: {"A":..,"m":[..],"levels":..,"span_L":[..],"first": file,"n": count}}."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import x1b_family as F
from boolflux.hub.common import load


def files_of(p):
    p = Path(p)
    if p.is_dir():
        return sorted(list(p.glob('*.bfx')) + list(p.glob('*.circ.txt')))
    return [p]


def main():
    a = sys.argv[1:]
    out = Path(a[0]); amax = 29; arch = []; paths = []
    i = 1
    while i < len(a):
        if a[i] == '--amax': amax = int(a[i + 1]); i += 2
        elif a[i] == '--archive': arch.append(a[i + 1]); i += 2
        else: paths.append(a[i]); i += 1
    fl = [f for p in paths for f in files_of(p)]
    for d in arch:
        ad = Path(d) / 'archive'
        for j in ad.glob('*.json'):
            if j.name == 'cells.json': continue
            try: r = json.loads(j.read_text())
            except Exception: continue
            if r.get('A', 99) <= amax and (ad / (r['id'] + '.bfx')).exists(): fl.append(ad / (r['id'] + '.bfx'))
    reg = json.loads(out.read_text()) if out.exists() else {}
    n = 0
    for f in fl:
        try:
            c = load(f)
            r = F.analyse_c(c)
        except Exception as e:
            print('skip', f, e); continue
        if r['m'][0] > amax: continue
        n += 1
        e = reg.get(r['span'])
        if e is None:
            reg[r['span']] = {'A': r['A_eff'], 'm': list(r['m']), 'levels': r['levels'], 'span_L': r['span_L'], 'first': str(f), 'n': 1}
        else:
            e['n'] += 1
            if list(r['m']) < e['m']: e['m'] = list(r['m']); e['first'] = str(f)
    out.write_text(json.dumps(reg, indent=0))
    by = {}
    for k, e in reg.items(): by.setdefault(e['A'], []).append(e)
    print('%d circuits read; registry %d spans; by A_eff: %s' % (n, len(reg), {A: len(v) for A, v in sorted(by.items())}))


if __name__ == '__main__':
    main()
