"""Check Boolean circuits against their function: python3 nonlinear/check.py [FILE_OR_DIR ...]

For every circuit file (``*.circ.txt``, ``*.ncff.txt``, ``*.slp``) under the given paths (default:
``nonlinear/nist`` and ``nonlinear/circuits``):

* parse it with every gate's own semantics (XOR, XNOR, AND, NOT; also OR, NAND, NOR);
* compute NIST's metrics (#AND, AND depth, #Gates, gate depth, #XOR, #XNOR) and compare them
  with the numbers in the file name and with the tallies in the file's header, if any;
* verify it twice by complete truth table, from the gate list and from its AND skeleton,
  against the function its folder or name designates (the AES S-box or inverse S-box by
  FIPS-197's definition, or the ``*.fn.json`` table in its folder), under both bit orders.

Exit status 1 if any circuit fails.  Standard library only.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from boolcirc import metrics as M, ncff, skeleton as S, truth  # noqa: E402

SUFFIXES = ('.circ.txt', '.ncff.txt', '.slp')
DEFAULT_DIRS = [HERE / 'nist', HERE / 'circuits']


def function_for(path):
    """The Function a circuit file must compute, from a ``*.fn.json`` in its folder or from
    its name (``aes-sbox``, ``aes-invsbox``, ``aes-sbox-fwd/-inv/-rev``)."""
    tables = sorted(path.parent.glob('*.fn.json'))
    if len(tables) > 1:          # several targets in one folder: the file name starts with the target's
        tables = [t for t in tables if path.name.startswith(t.name[:-len('.fn.json')])]
    if len(tables) == 1:
        d = json.loads(tables[0].read_text())
        return truth.Function.from_table(d['name'], d['n_inputs'], d['n_outputs'], d['table'],
                                         **{k: v for k, v in d.items()
                                            if k not in ('name', 'n_inputs', 'n_outputs', 'table')})
    if tables:
        raise ValueError('%s: several *.fn.json match' % path)
    name = path.name.lower()
    if name.startswith(('aes-invsbox', 'aes-sbox-inv', 'aes-sbox-rev')):
        return truth.aes_inv_sbox()
    if name.startswith('aes-sbox'):
        return truth.aes_sbox()
    return None


def check_file(path):
    """``[(circuit name, metrics, orders, problems)]`` for every circuit in the file."""
    out = []
    try:
        circuits = ncff.parse_file(path)
    except (ncff.FormatError, UnicodeDecodeError) as e:
        return [(path.name, None, [], ['cannot parse: %s' % e])]
    fn = function_for(path)
    for c in circuits:
        problems = []
        m = M.metrics(c)
        if m.dead:
            problems.append('dead gates: %s' % ' '.join(m.dead[:8]))
        if m.not_count:
            problems.append('note: %d NOT gates counted as gates and depth levels' % m.not_count)
        problems += M.check_name(path.name, m)
        problems += M.check_tallies(c, m)
        orders = []
        if fn is None:
            problems.append('no function known for this file (name or *.fn.json)')
        else:
            orders = truth.match(c, fn)
            if not orders:
                problems.append('not equivalent to %s under any bit order' % fn.name)
            sk = S.skeleton(c)
            sk_orders = truth.match_evaluator(sk.tables, c.n_inputs, fn)
            if sorted(sk_orders) != sorted(orders):
                problems.append('skeleton evaluation disagrees with the gate list')
            degenerate = sk.degenerate()
            if degenerate:
                problems.append('degenerate AND gates: %s' % degenerate)
        out.append((c.name, m, orders, problems))
    return out


def main(args):
    files = []
    for a in (args or DEFAULT_DIRS):
        p = pathlib.Path(a)
        if p.is_dir():
            files += sorted(f for f in p.rglob('*') if f.name.endswith(SUFFIXES))
        elif p.exists():
            files.append(p)
    bad = 0
    for f in files:
        for name, m, orders, problems in check_file(f):
            hard = [p for p in problems if not p.startswith('note:')]
            bad += bool(hard)
            status = 'ok ' if not hard else 'BAD'
            summary = m.summary() if m else ''
            print('%s %-60s %s  orders=%s' % (status, f.name, summary,
                                           ','.join('%s/%s' % o for o in orders) or '-'))
            for p in problems:
                print('      ' + p)
    print('%d circuit file(s), %d failing' % (len(files), bad))
    return 1 if bad or not files else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
