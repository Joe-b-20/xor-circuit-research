#!/usr/bin/env python3
"""P1 survey: every archived AES S-box circuit with A <= 28 and AD <= 5 (legal starts for T01/T03).

    python3 survey.py OUT.json

Scans the hub archives, results/aes, the study found/ folders, best-1400, T1 scratchpool, the
NIST pin. Verifies each on all 256 inputs (core), dedupes by gate-list hash, writes one row per
distinct circuit: tuple, path, sha256 of file, dedup key.  Prints the (G, GD) Pareto per AD class.
"""
import glob
import hashlib
import json
import os
import sys
from pathlib import Path

HOME = Path.home()
sys.path.insert(0, str(HOME / 'xcr-boolflux/nonlinear'))
from boolflux import core, targets  # noqa: E402

M = core.Model.load('nist')
TAB = targets.aes_sbox()

PATS = [
    'xs-campaigns/2026-11-14-hub/*/archive/*.bfx',
    'xcr-boolflux/nonlinear/boolflux/results/aes/*.circ.txt',
    'xcr-boolflux/nonlinear/nist/aes-sbox/*.circ.txt',
    'xs-campaigns/2026-11-15-study/best-1400/*.circ.txt',
    'xs-campaigns/2026-11-15-study/*/found/**/*.bfx',
    'xs-campaigns/2026-11-15-study/*/found/**/*.circ.txt',
    'xs-campaigns/2026-11-15-study/T1/scratchpool/**/*.bfx',
    'xs-campaigns/2026-11-15-study/T1/scratchpool/**/*.circ.txt',
    'xs-campaigns/2026-11-15-targets/*/found/*.circ.txt',
]


def load(p):
    t = Path(p).read_text()
    if p.endswith('.bfx'):
        return core.from_kernel(t)
    return core.read_ncff(t)


def main():
    out = sys.argv[1]
    files = []
    for pat in PATS:
        files += glob.glob(str(HOME / pat), recursive=True)
    files = sorted(set(files))
    print('files', len(files), flush=True)
    seen = {}
    bad = 0
    for i, f in enumerate(files):
        js = f[:-4] + '.json'
        if '/archive/' in f and f.endswith('.bfx') and Path(js).exists():
            try:
                r = json.loads(Path(js).read_text())
                if r['A'] > 28 or r['AD'] > 5: continue
            except Exception:
                pass
        try:
            c = load(f)
            m = c.metrics(M)
        except Exception:
            bad += 1
            continue
        if m['A'] > 28 or m['AD'] > 5:
            continue
        if c.value_table() != TAB:
            bad += 1
            continue
        key = hashlib.sha256(core.to_kernel(c).encode()).hexdigest()[:16]
        if key in seen:
            continue
        seen[key] = {'A': m['A'], 'AD': m['AD'], 'G': m['G'], 'GD': m['GD'], 'path': f,
                     'sha256': hashlib.sha256(Path(f).read_bytes()).hexdigest(), 'key': key}
    rows = sorted(seen.values(), key=lambda r: (r['AD'], r['G'], r['GD']))
    json.dump(rows, open(out, 'w'), indent=0)
    print('distinct A<=28 AD<=5:', len(rows), 'bad/unreadable:', bad)
    for ad in (4, 5):
        pts = sorted({(r['G'], r['GD']) for r in rows if r['AD'] == ad})
        front = [p for p in pts if not any(q != p and q[0] <= p[0] and q[1] <= p[1] for q in pts)]
        print('AD%d front' % ad, front)
        for gd in range(14, 28):
            n = [r for r in rows if r['AD'] == ad and r['GD'] == gd and r['G'] <= min([q[0] for q in pts if q[1] == gd] or [999]) + 4]
            if n:
                print('  AD%d GD%d: best G %d, %d circuits within +4' % (ad, gd, min(r['G'] for r in n), len(n)))


if __name__ == '__main__':
    main()
