"""P5: anatomy of an AD4 A32 circuit's last AND level: each operand as (x-linear part, AND atoms).

usage: python3 anat4.py FILE
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'P4'))
import circ  # noqa  (P4's reader / symbolic decomposition)


def main():
    gates = circ.read(sys.argv[1])
    if isinstance(gates, tuple): gates = gates[0]
    s = circ.symbolic(gates)
    lev = {f'x{i}': 0 for i in range(8)}
    for op, o, ins in gates:
        l = max(lev[i] for i in ins if i in lev)
        lev[o] = l + (1 if op == 'AND' else 0)
    top = max(lev.values())
    for op, o, ins in gates:
        if op != 'AND': continue
        parts = []
        for i in ins:
            atoms, c = s[i] if isinstance(s[i], tuple) else (s[i], 0)
            xs = sorted(a for a in atoms if a.startswith('x'))
            ands = sorted((a for a in atoms if not a.startswith('x')), key=lambda a: (lev[a], a))
            parts.append('%s[x:%s | a:%s]' % (i, '+'.join(xs) or '0', '+'.join('%s@%d' % (a, lev[a]) for a in ands) or '0'))
        print('L%d %s = %s' % (lev[o], o, '  &  '.join(parts)))


if __name__ == '__main__':
    main()
