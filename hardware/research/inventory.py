#!/usr/bin/env python3
"""Inventory every AES circuit on this machine: verify it, measure it, hash its structure.

    python3 hardware/research/inventory.py [ROOT ...] [-j N]   # default roots: ~/xs-campaigns ~/xcr-* ~/xor-circuit-research

Sources: NIST-format circuit files (``*.circ.txt``: S-box, inverse, direction-select, and linear
maps) and XORFlux record files (``g<G>-d<D>-<hash>.json`` with ``metadata.target``) for AES
MixColumns and InvMixColumns.  Every circuit is verified against its function independently of
the hardware pipeline (S-boxes: circuits/boolcirc truth tables against FIPS 197; linear maps:
GF(2) masks against the matrix file) and gets a *structure hash*: a canonical hash of its gate DAG
(inputs by bit, commutative operands sorted, dead gates included), so two files with the same
gates under other names or another order hash alike, and two different topologies never do,
whatever their metrics.

Output (hardware/research/inventory/): pool.jsonl.gz, one line per distinct structure
(function, metrics, hash, number of files, up to 5 source paths with their provenance), and
summary.json (counts per function and source, verification failures).  The pools index files
of this machine and are not committed; summary.json and summary-v1.json (the version-1 hash
the sample was drawn with) are.
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures as cf
import gzip
import hashlib
import json
import os
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from hwbench import design as D  # noqa: E402
from boolcirc import metrics as M, ncff, truth  # noqa: E402


LINEAR = ('aes-mixcolumns', 'aes-invmixcolumns')
OUT = HERE / 'inventory'


def h16(s):
    return hashlib.sha1(s.encode()).hexdigest()[:16]


HASH_VERSION = 2


def fold(op, args):
    """A gate with a constant operand as the benchmark builds it (verilog.simplified_gates):
    ('NOT', a), ('BUF', a) or ('CONST', v); other gates unchanged."""
    if not any(a in ('0', '1') for a in args):
        return op, args
    others = [a for a in args if a not in ('0', '1')]
    if op == 'NOT':
        return 'CONST', ('1' if args[0] == '0' else '0',)
    if not others:
        a, b = (int(v) for v in args)
        return 'CONST', (str({'AND': a & b, 'XOR': a ^ b, 'XNOR': 1 ^ a ^ b}[op]),)
    c = int([a for a in args if a in ('0', '1')][0])
    if op == 'AND':
        return ('BUF', (others[0],)) if c else ('CONST', ('0',))
    return ('NOT' if (op == 'XNOR') ^ c else 'BUF', (others[0],))


def structure_hash(n_in, gates, outputs):
    """Canonical hash of the gate DAG as the benchmark builds it.

    gates: [(op, out, (args...))] over names; inputs are 'i<bit>'; outputs: names in bit order.
    Constant operands are folded as the benchmark folds them (a copy becomes an alias), each
    node is hashed by its operation and its operands' hashes (commutative: sorted), and the
    circuit by the multiset of (node hash, fanout) and the outputs' node hashes.  Renaming
    wires or reordering gates never changes the hash; two DAGs that differ only in which of two
    identical duplicate gates feeds a consumer can still collide (version 2 tells them apart
    when their fanouts differ)."""
    node = {('i%d' % b): 'i%d' % b for b in range(n_in)}
    node['0'], node['1'] = 'c0', 'c1'
    hs = []
    fan = {}
    alias = {}

    def res(a):
        while a in alias:
            a = alias[a]
        return a
    for op, out, args in gates:
        op, args = fold(op, tuple(res(a) for a in args))
        if op == 'BUF':
            alias[out] = args[0]
            node[out] = node[args[0]]
            continue
        if op == 'CONST':
            alias[out] = args[0]
            node[out] = 'c' + args[0]
            continue
        hh = h16('%s(%s)' % (op, ','.join(sorted(node[a] for a in args))))
        node[out] = hh
        hs.append((hh, out))
        for a in args:
            fan[a] = fan.get(a, 0) + 1
    outputs = [res(o) for o in outputs]
    for o in outputs:
        fan[o] = fan.get(o, 0) + 1
    multiset = sorted('%s:%d' % (hh, fan.get(out, 0)) for hh, out in hs)
    return h16('v%d|' % HASH_VERSION + '|'.join(multiset) + '#' + ','.join(node[o] for o in outputs))


def provenance(path):
    p = str(path)
    home = str(pathlib.Path.home())
    rel = p[len(home) + 1:] if p.startswith(home) else p
    top = rel.split('/')[0]
    if top == 'xs-campaigns':
        return 'campaign:' + rel.split('/')[1]
    return 'checkout:' + top


_FN = {}


def functions():
    if not _FN:
        _FN['aes-sbox'] = truth.aes_sbox()
        _FN['aes-invsbox'] = truth.aes_inv_sbox()
        _FN['aes-sbox-sel'] = truth.aes_sbox_sel()
    return _FN


def read_boolean(path):
    """A NIST-format file: its function is found by trying the candidates, not from its name
    (many campaign files are called 'circuit', 'best', ...): exactly one function and one bit
    order must match."""
    c = ncff.load(path)
    c.validate()
    m = M.metrics(c)
    if m.other:
        raise ValueError('gates other than AND/XOR/XNOR/NOT')
    if not m.and_count and not m.not_count and c.n_inputs == 32 and c.n_outputs == 32:
        return read_linear_ncff(c, m)
    cands = {(8, 8): ('aes-sbox', 'aes-invsbox'), (9, 8): ('aes-sbox-sel',)}.get(
        (c.n_inputs, c.n_outputs), ())
    found = []
    for fn in cands:
        for orders in truth.match(c, functions()[fn]):
            found.append((fn, orders))
    if len(found) != 1:
        raise ValueError('matches %d (function, bit order) pairs' % len(found))
    (fn, (io, oo)), = found
    bits_in = list(range(c.n_inputs)) if io == 'lsb' else [c.n_inputs - 1 - i for i in range(c.n_inputs)]
    bits_out = list(range(c.n_outputs)) if oo == 'lsb' else [c.n_outputs - 1 - i for i in range(c.n_outputs)]
    rename = {w: 'i%d' % bits_in[i] for i, w in enumerate(c.inputs)}
    gates = [(g.op, 'w:' + g.out, tuple(rename.get(a, a if a in '01' else 'w:' + a) for a in g.args))
             for g in c.gates]
    outs = [None] * c.n_outputs
    for i, w in enumerate(c.outputs):
        outs[bits_out[i]] = rename.get(w, 'w:' + w)
    return {'function': fn, 'kind': 'boolean', 'A': m.and_count, 'AD': m.and_depth, 'G': m.gates,
            'GD': m.gate_depth, 'XNOR': m.xnor, 'NOT': m.not_count, 'dead': len(m.dead),
            'hash': structure_hash(c.n_inputs, gates, outs)}


def read_linear_ncff(c, m):
    """A 32x32 XOR circuit in NIST format: AES MixColumns or InvMixColumns, inputs in file order."""
    val = {w: 1 << i for i, w in enumerate(c.inputs)}
    for g in c.gates:
        if g.op != 'XOR':
            raise ValueError('linear circuit with %s' % g.op)
        val[g.out] = val[g.args[0]] ^ val[g.args[1]]
    got = [val[o] for o in c.outputs]
    for fn in LINEAR:
        if got == matrix(fn)[0]:
            break
    else:
        raise ValueError('32x32 XOR circuit of another map')
    rename = {w: 'i%d' % i for i, w in enumerate(c.inputs)}
    gates = [('XOR', 'w:' + g.out, tuple(rename.get(a, 'w:' + a) for a in g.args)) for g in c.gates]
    outs = [rename.get(w, 'w:' + w) for w in c.outputs]
    return {'function': fn, 'kind': 'linear', 'A': 0, 'AD': 0, 'G': m.gates, 'GD': m.gate_depth,
            'XNOR': 0, 'NOT': 0, 'dead': len(m.dead), 'hash': structure_hash(32, gates, outs)}


_MAT = {}


def matrix(fn):
    if fn not in _MAT:
        _MAT[fn] = D.read_matrix(D.REPO / 'circuits' / fn / (fn + '.mat.txt'))
    return _MAT[fn]


def read_record(path):
    j = json.loads(pathlib.Path(path).read_text())
    md = j.get('metadata') or {}
    fn = md.get('target')
    if fn not in LINEAR:
        return None
    n = j['inputCount']
    rows, consts, ncols = matrix(fn)
    if n != ncols or any(consts):
        raise ValueError('unexpected shape')
    mask = [1 << i for i in range(n)]
    depth = [0] * n
    gates = []
    for k, (a, b) in enumerate(j['gates']):
        mask.append(mask[a] ^ mask[b])
        depth.append(1 + max(depth[a], depth[b]))
        gates.append(('XOR', 'w%d' % (n + k), tuple('i%d' % x if x < n else 'w%d' % x for x in (a, b))))
    outs = j['outputSignals']
    if [mask[o] for o in outs] != rows:
        raise ValueError('not the matrix')
    gd = max(depth[o] for o in outs)
    if len(j['gates']) != j['gateCount'] or gd != j['depth']:
        raise ValueError('metrics differ from the record')
    names = ['i%d' % o if o < n else 'w%d' % o for o in outs]
    return {'function': fn, 'kind': 'linear', 'A': 0, 'AD': 0, 'G': len(j['gates']), 'GD': gd,
            'XNOR': 0, 'NOT': 0, 'dead': 0, 'hash': structure_hash(n, gates, names)}


def work(path):
    try:
        r = read_boolean(path) if path.endswith('.circ.txt') else read_record(path)
    except Exception as e:      # counted, not fatal
        return ('fail', path, '%s: %s' % (type(e).__name__, str(e).replace(path, '')[:100]))
    if r is None:
        return ('skip', path, None)
    if r['kind'] == 'linear' and r['function'] not in LINEAR:
        return ('skip', path, None)
    return ('ok', path, r)


def files(roots):
    rec = re.compile(r'^g\d+-d\d+-[0-9a-f]+\.json$')
    for root in roots:
        for dp, dn, fs in os.walk(root):
            dn[:] = [x for x in dn if x != '.git']
            for f in fs:
                if f.endswith('.circ.txt') or rec.match(f):
                    yield os.path.join(dp, f)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('roots', nargs='*')
    ap.add_argument('-j', '--jobs', type=int, default=os.cpu_count())
    a = ap.parse_args(argv)
    home = pathlib.Path.home()
    roots = a.roots or [str(home / 'xs-campaigns')] + sorted(str(p) for p in home.glob('xcr-*')) \
        + [str(home / 'xor-circuit-research')]
    paths = sorted(set(files(roots)))
    print('%d files' % len(paths), flush=True)
    pool = {}
    stats = collections.Counter()
    fails = collections.Counter()
    fail_examples = {}
    with cf.ProcessPoolExecutor(a.jobs) as ex:
        for i, (st, path, r) in enumerate(ex.map(work, paths, chunksize=256)):
            stats[st] += 1
            if st == 'fail':
                key = r[:60]
                fails[key] += 1
                fail_examples.setdefault(key, (path, r))
                continue
            if st != 'ok':
                continue
            k = (r['function'], r['hash'])
            e = pool.get(k)
            if e is None:
                e = pool[k] = dict(r, n_files=0, sources=[], provenance=set())
            e['n_files'] += 1
            e['provenance'].add(provenance(path))
            if len(e['sources']) < 5:
                e['sources'].append(path)
            if i % 50000 == 0:
                print('  %d/%d' % (i, len(paths)), flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUT / 'pool.jsonl.gz', 'wt') as f:
        for k in sorted(pool):
            e = pool[k]
            e['provenance'] = sorted(e['provenance'])
            f.write(json.dumps(e, sort_keys=True) + '\n')
    per = collections.Counter(e['function'] for e in pool.values())
    keys = collections.defaultdict(set)
    for e in pool.values():
        keys[e['function']].add((e['A'], e['AD'], e['G'], e['GD']))
    summary = {'roots': roots, 'files': len(paths), 'status': dict(stats),
               'failures': dict(fails), 'failure_examples': fail_examples,
               'structures': dict(per), 'metric_keys': {f: len(v) for f, v in keys.items()}}
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=1, sort_keys=True) + '\n')
    print(json.dumps({k: summary[k] for k in ('files', 'status', 'failures', 'structures',
                                               'metric_keys')}, indent=1))


if __name__ == '__main__':
    main()
