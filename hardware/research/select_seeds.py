#!/usr/bin/env python3
"""Which circuits get seeded repeats (lists/seeds.txt, split by size into seeds-small.txt and
seeds-large.txt like the base run), by a fixed rule:

  1. per function, the 2 same-metric groups with a baseline (published or NIST) member that have
     the most members: every member;
  2. the first pair of the benchmark;
  3. per function, library, flow and measure (delay, ADP, power), the dominance inversion with the
     largest apparent gain in the base run (analysis.json, inversions_top): both circuits.
     These are the apparent wins most likely to be winner's-curse noise, so they are exactly the
     ones to repeat.

    python3 hardware/research/select_seeds.py

It was run once, on the base run of the circuits with G < 400 and of the screen (before the
41 larger circuits had finished); lists/seeds.txt is that choice.  Run on the final analysis it
can choose differently.
"""
from __future__ import annotations

import collections
import csv
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
RES = HERE / 'results'
LARGE_G = 400       # as sample.py: circuits this large run on Nangate45 and SKY130 preserve only


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--res', default=str(RES), help='folder with table.csv and analysis.json')
    ap.add_argument('--out', default=str(HERE / 'lists'), help='where seeds*.txt are written')
    args = ap.parse_args(argv)
    res = pathlib.Path(args.res).resolve()
    rows = list(csv.DictReader(open(res / 'table.csv')))
    a = json.loads((res / 'analysis.json').read_text())
    file_of = {r['circuit']: r['file'] for r in rows}
    members = collections.defaultdict(set)
    has_base = set()
    iso_keys = {(r['function'], r['key']) for r in rows if r['part'] == 'iso'}
    for r in rows:
        if (r['function'], r['key']) in iso_keys:
            members[(r['function'], r['key'])].add(r['circuit'])
            if r['part'] == 'baseline':
                has_base.add((r['function'], r['key']))
    chosen = {}
    for fn in sorted({k[0] for k in members}):
        ks = sorted((k for k in members if k[0] == fn and k in has_base),
                    key=lambda k: (-len(members[k]), k[1]))[:2]
        for k in ks:
            for c in sorted(members[k]):
                chosen.setdefault(c, 'iso %s %s' % k)
    for c in ('ours--aes-invsbox-a40-ad4-g134-gd12-xx94-41', 'nist--aes-invsbox-a45-ad4-g141-gd12-xx96-25'):
        chosen.setdefault(c, 'first pair')
    best = {}
    for t in a['inversions_top']:
        if t['measure'] == 'area' and t['flow'] == 'preserve':
            continue
        k = (t['function'], t['platform'], t['flow'], t['measure'])
        if k not in best or t['gain'] > best[k]['gain']:
            best[k] = t
    for k, t in sorted(best.items()):
        for c in (t['worse_logically'], t['better_logically']):
            chosen.setdefault(c, 'inversion %s %s %s %s' % k)
    lines = ['%s  # %s' % (file_of[c], why) for c, why in sorted(chosen.items())]
    out = pathlib.Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / 'seeds.txt').write_text('\n'.join(lines) + '\n')
    gates = {r['file']: int(r['key'].split('/')[2]) for r in rows}
    small = [l for l in lines if gates[l.split()[0]] < LARGE_G]
    large = [l for l in lines if gates[l.split()[0]] >= LARGE_G]
    (out / 'seeds-small.txt').write_text('\n'.join(small) + '\n')
    (out / 'seeds-large.txt').write_text('\n'.join(large) + '\n')
    print(len(chosen), 'circuits;', collections.Counter(w.split()[0] for w in chosen.values()))


if __name__ == '__main__':
    main()
