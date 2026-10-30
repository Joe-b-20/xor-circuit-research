"""Load the 32x32 GF(2) matrix from ../matrix.txt and expose it as TARGETS.

TARGETS[r] is the mask of output row r: bit c is set iff M[r][c] = 1, so
output r is the XOR of the inputs whose column index appears in TARGETS[r].
Row order is the row order of matrix.txt, which is the order the certificate's
row/variable indices were built in -- do not sort it.

Standard library only.  This module is the ONLY place the model touches the
matrix; point --matrix at another file and the whole model rebuilds for it.
"""
import os

DEFAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'matrix.txt')


def load(path=None):
    path = path or os.environ.get('BOUNDS_MATRIX') or DEFAULT
    rows = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            if any(ch not in '01' for ch in line):
                raise SystemExit('%s: row %r is not a 0/1 string' % (path, line))
            rows.append(line)
    n = len(rows[0])
    if any(len(r) != n for r in rows):
        raise SystemExit('%s: rows have unequal length' % path)
    return [sum(1 << c for c in range(n) if row[c] == '1') for row in rows], n


TARGETS, NCOL = load()
