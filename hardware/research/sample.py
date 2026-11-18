#!/usr/bin/env python3
"""A reproducible sample of the inventory, written as candidate circuit files.

    python3 hardware/research/sample.py            # seed 20261118

Two parts, per function, both drawn with a fixed seed from the distinct structures of
inventory/pool-v1.jsonl.gz (the inventory before its structure hash folded constant operands;
the candidate names carry those version-1 hashes) that are not already in the benchmark (the 340 published and NIST
circuits, whose results are in hardware/build/):

* iso: same-metric groups.  The metric keys (A, AD, G, GD) with at least MIN_GROUP distinct
  structures (baseline ones counted), ranked: the keys of published or NIST circuits first,
  then the largest groups; ISO_KEYS keys per function, ISO_PER structures from each.
* spread: the whole metric space, worse circuits included.  Structures are grouped into cells
  (A, AD, GD, G decile of the function); cells are visited in seeded random order, one structure
  each, round after round, until SPREAD_N structures.

Output: candidates/<function>/<name>.circ.txt (name carries the metrics and the structure hash),
sample.json (every candidate: part, metrics, hash, source files, provenance), and the run lists
lists/candidates.txt, candidates-small.txt (G < LARGE_G) and candidates-large.txt.

It needs the local campaign archives the pool points to; the committed candidates/ and
sample.json are its output of 2026-11-18.
"""
from __future__ import annotations

import collections
import gzip
import json
import pathlib
import random
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import inventory as I  # noqa: E402
import bench  # noqa: E402
from boolcirc import ncff  # noqa: E402

SEED = 20261118
LARGE_G = 400       # circuits this large run on Nangate45 and SKY130 preserve only (run_all.sh)
MIN_GROUP = 5
ISO_KEYS = 8
ISO_PER = 8
SPREAD_N = {'aes-mixcolumns': 120, 'aes-invmixcolumns': 120, 'aes-sbox': 150,
            'aes-invsbox': 150, 'aes-sbox-sel': 120}


def key(e):
    return (e['A'], e['AD'], e['G'], e['GD'])


def name_for(e):
    if e['kind'] == 'linear':
        return '%s-xor%d-depth%d-h%s' % (e['function'], e['G'], e['GD'], e['hash'])
    return '%s-a%d-ad%d-g%d-gd%d-h%s' % (e['function'], e['A'], e['AD'], e['G'], e['GD'], e['hash'])


def write_candidate(e, path):
    src = e['sources'][0]
    note = ['Candidate of the hardware study (hardware/research/sample.py), not a published circuit',
            'Structure hash %s; source: %s' % (e['hash'], src.replace(str(pathlib.Path.home()), '~'))]
    if src.endswith('.circ.txt'):
        c = ncff.load(src)
    else:
        j = json.loads(pathlib.Path(src).read_text())
        n = j['inputCount']
        wire = ['x%d' % i for i in range(n)] + ['t%d' % (k + 1) for k in range(len(j['gates']))]
        gates = [ncff.Gate('XOR', wire[n + k], (wire[a], wire[b])) for k, (a, b) in enumerate(j['gates'])]
        c = ncff.Circuit('x', wire[:n], [wire[o] for o in j['outputSignals']], gates)
    c.name = name_for(e)
    c.internal = None
    c.validate()
    path.write_text(ncff.format_circuit(c, comments=note))
    # the written file is the same structure as its source (both hashed by the current
    # inventory, so this holds whatever hash version the pool was made with)
    r = I.read_boolean(str(path))
    s = I.read_boolean(src) if src.endswith('.circ.txt') else I.read_record(src)
    if (r['function'], r['hash'], key(r)) != (s['function'], s['hash'], key(e)):
        raise RuntimeError('candidate %s does not round-trip' % path)


def main():
    rng = random.Random(SEED)
    pool = [json.loads(l) for l in gzip.open(HERE / 'inventory' / 'pool-v1.jsonl.gz', 'rt')]
    base = {}
    for f in bench.expand(bench.suite('all')):
        r = I.read_boolean(str(f))
        base[(r['function'], r['hash'])] = f
    base_keys = {(fn, key(I.read_boolean(str(f)))) for (fn, _), f in base.items()}
    by = collections.defaultdict(list)
    for e in pool:
        by[e['function']].append(e)
    chosen = []
    for fn in sorted(by):
        es = sorted(by[fn], key=lambda e: e['hash'])
        groups = collections.defaultdict(list)
        for e in es:
            groups[key(e)].append(e)
        ok = [k for k, v in groups.items() if len(v) >= MIN_GROUP]
        ok.sort(key=lambda k: (0 if (fn, k) in base_keys else 1, -len(groups[k]), k))
        taken = set()
        for k in ok[:ISO_KEYS]:
            fresh = [e for e in groups[k] if (fn, e['hash']) not in base]
            for e in rng.sample(fresh, min(ISO_PER, len(fresh))):
                chosen.append(dict(e, part='iso'))
                taken.add(e['hash'])
        Gs = sorted(e['G'] for e in es)
        dec = [Gs[min(len(Gs) - 1, len(Gs) * q // 10)] for q in range(1, 10)]
        cells = collections.defaultdict(list)
        for e in es:
            if (fn, e['hash']) in base or e['hash'] in taken:
                continue
            cells[(e['A'], e['AD'], e['GD'], sum(e['G'] > d for d in dec))].append(e)
        order = sorted(cells)
        rng.shuffle(order)
        for c in order:
            rng.shuffle(cells[c])
        n = 0
        while n < SPREAD_N[fn] and any(cells[c] for c in order):
            for c in order:
                if cells[c] and n < SPREAD_N[fn]:
                    chosen.append(dict(cells[c].pop(), part='spread'))
                    n += 1
    out = HERE / 'candidates'
    if out.exists():
        shutil.rmtree(out)
    lines = []
    for e in chosen:
        d = out / e['function']
        d.mkdir(parents=True, exist_ok=True)
        p = d / (name_for(e) + '.circ.txt')
        write_candidate(e, p)
        e['file'] = p.relative_to(HERE.parents[1]).as_posix()
        lines.append(e['file'])
    (HERE / 'sample.json').write_text(json.dumps(
        {'seed': SEED, 'iso_keys': ISO_KEYS, 'iso_per': ISO_PER, 'min_group': MIN_GROUP,
         'spread_n': SPREAD_N, 'candidates': chosen}, indent=1, sort_keys=True) + '\n')
    lists = HERE / 'lists'
    lists.mkdir(exist_ok=True)
    (lists / 'candidates.txt').write_text('\n'.join(lines) + '\n')
    big = {e['file'] for e in chosen if e['G'] >= LARGE_G}
    (lists / 'candidates-small.txt').write_text('\n'.join(l for l in lines if l not in big) + '\n')
    (lists / 'candidates-large.txt').write_text('\n'.join(l for l in lines if l in big) + '\n')
    cnt = collections.Counter((e['function'], e['part']) for e in chosen)
    for k in sorted(cnt):
        print(k, cnt[k])
    print(len(chosen), 'candidates')


if __name__ == '__main__':
    main()
