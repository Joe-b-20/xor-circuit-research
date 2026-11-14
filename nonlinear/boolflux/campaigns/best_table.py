#!/usr/bin/env python3
"""Best AES S-box circuits found so far, as NIST-style tables.

    python3 nonlinear/boolflux/campaigns/best_table.py [--out DIR] [--md FILE]

Collects every candidate (results/aes, each track's found/, track E's admitted pools), keeps the
(A, AD, G, GD) tuples that no published circuit (pinned NIST set) dominates and no other candidate
strictly dominates, re-verifies each survivor with both verifiers on all 256 inputs
(aes_check.check), copies it to DIR with a NIST-style name, and prints tables in NIST's categories
plus the published best within the same caps.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[1]))
import aes_check as AC                     # noqa: E402
from boolflux import core                  # noqa: E402

C = Path.home() / 'xs-campaigns' / '2026-11-13-aes'
SOURCES = [HERE.parent / 'results' / 'aes']
GLOBS = ['D/found/*.circ.txt', 'E/found/*.circ.txt', 'F/found/*.circ.txt', 'main/**/best.circ.txt',
         'E/long1/*/admitted/*.bfx', 'E/low1/**/admitted/*.bfx', 'C/found/*.circ.txt']


def candidates():
    files = []
    for d in SOURCES:
        files += sorted(d.glob('*.circ.txt'))
    for g in GLOBS:
        files += sorted(C.glob(g))
    return [f for f in files if '.check.' not in f.name]


def le(p, q):
    return all(a <= b for a, b in zip(p, q))


def main():
    out = Path(sys.argv[sys.argv.index('--out') + 1]) if '--out' in sys.argv else C / 'best'
    md = Path(sys.argv[sys.argv.index('--md') + 1]) if '--md' in sys.argv else out / 'BEST.md'
    out.mkdir(parents=True, exist_ok=True)
    model = core.Model.load('nist')
    pub = AC.published()
    seen = {}
    for f in candidates():
        try:
            c = core.from_kernel(f.read_text()) if f.suffix == '.bfx' else core.read_ncff(str(f))
            m = c.metrics(model)
        except Exception:
            continue
        t = (m['A'], m['AD'], m['G'], m['GD'])
        if t not in seen:
            seen[t] = (f, c, m)
    new = {t: v for t, v in seen.items() if not any(le(u, t) for u, _ in pub)}
    pareto = {t: v for t, v in new.items() if not any(u != t and le(u, t) for u in new)}
    rows = []
    for t, (f, c, m) in sorted(pareto.items(), key=lambda kv: (kv[0][3], kv[0][2])):
        c.name = 'aes-sbox-a%d-ad%d-g%d-gd%d' % t
        c.in_names = ['x%d' % i for i in range(8)]; c.out_names = ['y%d' % i for i in range(8)]
        cnt = dict(m['counts'])
        xor, xnor, nt = cnt.get('XOR', 0), cnt.get('XNOR', 0), cnt.get('NOT', 0)
        name = 'aes-sbox-a%d-ad%d-g%d-gd%d-xx%d-%d.circ.txt' % (t + (xor + xnor + nt, xnor + nt))
        dst = out / name
        dst.write_text(core.write_ncff(c, model, comments=['BoolFlux candidate; source %s' % f]))
        r = AC.check(dst)
        if not r['ok']:
            print('VERIFICATION FAILED', f, r.get('errors')); continue
        rows.append((t, xor, xnor + nt, name, str(f).replace(str(Path.home()), '~'), r))
    cats = [('S-box with 29 <= #AND <= 31 (published circuits here have G >= 124)', lambda t: 29 <= t[0] <= 31),
            ('S-box with #AND = 28', lambda t: t[0] == 28),
            ('S-box with #AND = 32..36 / AD >= 4', lambda t: 32 <= t[0] <= 36 and t[1] >= 4),
            ('S-box with #AND <= 36 / AD3', lambda t: t[0] <= 36 and t[1] == 3),
            ('S-box with #AND > 36 (gate depth traded for ANDs)', lambda t: t[0] > 36)]
    L = ['# Best BoolFlux AES S-box circuits so far (not dominated by the pinned NIST set %s)' % json.load(open(AC.NIST / 'MANIFEST.json'))['commit'][:7], '', '',
         'Every row: verified by two independent implementations on all 256 inputs, NIST gate library',
         '{AND, XOR, XNOR, NOT}, every gate counted. "Published best" = fewest gates among published',
         'circuits within the same caps (#AND <= A, AND depth <= AD, gate depth <= GD); ** = better.', '']
    for title, pred in cats:
        sel = [r for r in rows if pred(r[0])]
        if not sel: continue
        L += ['### ' + title, '',
              '| File | #AND (A) | AND depth | #Gates (G) | Gate depth | XX (x+x\') | #XOR | #XNOR | published best within the same caps |',
              '|---|---:|---:|---:|---:|---:|---:|---:|---|']
        for t, xor, xnor, name, src, r in sel:
            b = r['best_at_a_ad_gd_caps']
            pb = 'none' if not b else '%d (A%d AD%d GD%d)' % (b['tuple'][2], b['tuple'][0], b['tuple'][1], b['tuple'][3])
            L.append('| %s | %d | %d | **%d** | %d | %d | %d | %d | %s |' % (name, t[0], t[1], t[2], t[3], xor + xnor, xor, xnor, pb))
        L.append('')
    L += ['### Fewest gates at each gate-depth cap', '', '| GD <= | published best (A AD G GD) | ours (A AD G GD) |', '|---|---|---|']
    for d in range(10, 33):
        p = min((u for u, _ in pub if u[3] <= d), key=lambda u: (u[2], u), default=None)
        o = min((r[0] for r in rows if r[0][3] <= d), key=lambda u: (u[2], u), default=None)
        if o and p and o[2] < p[2]:
            L.append('| %d | %s | **%s** |' % (d, ' '.join(map(str, p)), ' '.join(map(str, o))))
    L += ['', 'Sources: ' + ', '.join(sorted({r[4].split('/')[3] if r[4].startswith('~/xs-') else 'results/aes' for r in rows}))]
    text = '\n'.join(L) + '\n'
    md.write_text(text)
    print(text)


if __name__ == '__main__':
    main()
