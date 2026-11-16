"""Render a kernel move trace: the improving moves, with the circuit before and after each.

    python3 search/nonlinear/boolflux/bench/show_trace.py MOVES.txt [--max N]

MOVES.txt is the file written by the gate kernel's `tracemoves` setting; for every improving
move the kernel also wrote MOVES.txt.it<N>.before / .after (kernel circuit format).  Signals are
printed as s<k> (inputs s0..s(n-1), gate j = s(n+j)) as in the trace line; for the after-circuit
the gates are renumbered by the rebuild, so the diff lists gates by function: the multiset of
(op, operand functions) removed and added, with each signal shown by its truth table in hex.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from boolflux import core   # noqa: E402

NAMES = {v: k for k, v in core.OPS.items()}
KIND = []


def show(c, label):
    tabs = c.tables(); n = c.n
    w = (1 << n) // 4 if n >= 2 else 1
    print('  %s: G %d  A %d  GD %d' % (label, len(c.gates), c.metrics()['A'], c.metrics()['GD']))
    for j, (op, a, b) in enumerate(c.gates):
        args = 's%d' % a if op == 3 else 's%d, s%d' % (a, b)
        outs = [k for k, s in enumerate(c.outputs) if s == n + j]
        print('    s%-3d = %-5s(%s)%s   tt=%0*x' % (n + j, NAMES.get(op, op), args,
              ('   -> y%s' % ','.join(map(str, outs))) if outs else '', w, tabs[n + j]))


def by_function(c):
    t = c.tables()
    return {(c.gates[j][0], tuple(sorted({t[c.gates[j][1]], t[c.gates[j][2]]}))): t[c.n + j] for j in range(len(c.gates))}


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print(__doc__.strip()); sys.exit(0 if len(sys.argv) > 1 and sys.argv[1] in ('-h', '--help') else 2)
    path = Path(sys.argv[1]); mx = int(sys.argv[sys.argv.index('--max') + 1]) if '--max' in sys.argv else 99
    shown = 0
    for line in path.read_text().splitlines():
        it = int(line.split()[1])
        bf = Path(str(path) + '.it%d.before' % it)
        if not bf.exists(): continue
        print(line)
        b = core.from_kernel(bf.read_text()); a = core.from_kernel(Path(str(path) + '.it%d.after' % it).read_text())
        assert b.value_table() == a.value_table()
        if len(b.gates) <= 12:
            show(b, 'before'); show(a, 'after')
        fb, fa = by_function(b), by_function(a)
        rem = [k for k in fb if k not in fa]; add = [k for k in fa if k not in fb]
        tb = b.tables(); ta = a.tables()
        print('  removed gates (op, operand truth tables): %d; added: %d' % (len(rem), len(add)))
        for tag, lst in (('-', rem), ('+', add)):
            for op, ops in lst:
                print('    %s %-5s %s' % (tag, NAMES.get(op, op), ' '.join('%x' % o for o in ops)))
        print('  ANDs before %d, after %d; same function on all %d inputs: yes' % (b.metrics()['A'], a.metrics()['A'], 1 << b.n))
        # what happened to the nonlinear gates: by output function
        nl = core.NONLINEAR_OPS
        ob = {}; oa = {}
        for (op, ops_), out in fb.items():
            if op in nl: ob.setdefault(out, []).append(ops_)
        for (op, ops_), out in fa.items():
            if op in nl: oa.setdefault(out, []).append(ops_)
        gone = [o for o in ob if o not in oa]; new = [o for o in oa if o not in ob]
        rewired = [o for o in ob if o in oa and sorted(ob[o]) != sorted(oa[o])]
        print('  AND functions: %d no longer computed, %d new, %d rewired (same output, different operands)'
              % (len(gone), len(new), len(rewired)))
        KIND.append((it, len(gone), len(new), len(rewired), len(b.gates) - len(a.gates)))
        shown += 1
        if shown >= mx: break
    if KIND:
        print('summary: %d improving moves; moves that replaced an AND function %d, added an AND function %d, rewired an AND %d, XOR-only %d'
              % (len(KIND), sum(1 for k in KIND if k[1]), sum(1 for k in KIND if k[2]), sum(1 for k in KIND if k[3]),
                 sum(1 for k in KIND if not (k[1] or k[2] or k[3]))))


if __name__ == '__main__':
    main()
