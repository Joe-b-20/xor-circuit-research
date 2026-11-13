"""Linear algebra over GF(2) on bit vectors held as Python ints.

A vector is an int (bit i = coordinate i); a truth table of 2^n bits is a vector too, so the
same code answers "is this function in the span of those" for functions and for linear forms.
``Basis`` keeps an echelon basis (pivot = highest set bit) that grows one vector at a time and,
when ``track`` is on, remembers how each basis vector was built from the inserted ones, which
makes ``express`` return the combination of inserted vectors that equals a query.

``reduce`` is a *canonical* reduction: it clears every pivot bit, top down, so ``reduce(v)`` is
the same for all vectors of a coset ``v + span`` and ``reduce(u ^ v) == reduce(u) ^ reduce(v)``.
That makes it usable as a coset key and in quotient-space linear algebra (ranks modulo a
subspace, solving modulo a subspace), not only as a membership test.  (An earlier version
stopped at the first non-pivot leading bit, which is a membership test but not canonical; the
skeleton experiments of 2026-10-30 ran into that.)
"""
from __future__ import annotations


class Basis:
    """Incremental echelon basis of GF(2) vectors.

    ``add(v)`` returns True when v was independent of the basis so far.  ``reduce(v)`` returns
    v reduced against the basis (0 iff v is in the span).  With ``track=True``, ``express(v)``
    returns the mask of inserted vectors (bit k = k-th successful or failed insertion, in
    insertion order) whose XOR is v, or None when v is outside the span.
    """
    __slots__ = ('rows', 'combo', 'track', 'count', '_sorted')

    def __init__(self, vectors=(), track=False):
        self.rows = {}        # pivot bit -> vector
        self.combo = {}       # pivot bit -> combination mask over inserted vectors
        self.track = track
        self.count = 0        # vectors inserted so far (independent or not)
        self._sorted = None   # pivots, highest first (cache)
        for v in vectors:
            self.add(v)

    @property
    def rank(self):
        return len(self.rows)

    def _reduce(self, v, c=0):
        rows = self.rows
        combo = self.combo
        # Pivots are the rows' highest bits, so clearing them from the top down never re-sets a
        # pivot already cleared: the result has no pivot bit set and is canonical for the coset.
        for p in self._pivots():
            if v >> p & 1:
                v ^= rows[p]
                if self.track:
                    c ^= combo[p]
        return v, c

    def _pivots(self):
        if self._sorted is None:
            self._sorted = sorted(self.rows, reverse=True)
        return self._sorted

    def reduce(self, v):
        """The canonical representative of ``v + span`` (0 iff v is in the span); linear in v."""
        return self._reduce(v)[0]

    canon = reduce

    def contains(self, v):
        return self._reduce(v)[0] == 0

    def add(self, v):
        """Insert v; True iff it enlarged the span."""
        c = 1 << self.count if self.track else 0
        self.count += 1
        v, c = self._reduce(v, c)
        if v == 0:
            return False
        p = v.bit_length() - 1
        self.rows[p] = v
        self._sorted = None
        if self.track:
            self.combo[p] = c
        return True

    def rank_modulo(self, vectors):
        """Rank of ``vectors`` modulo this basis's span (dimension of their span in the quotient)."""
        return Basis(self.reduce(v) for v in vectors).rank

    def express(self, v):
        """Mask over inserted vectors whose XOR is v, or None (needs ``track=True``)."""
        if not self.track:
            raise ValueError('express needs a tracking basis')
        v, c = self._reduce(v, 0)
        return None if v else c

    def vectors(self):
        """The basis vectors (echelon form), highest pivot first."""
        return [self.rows[p] for p in sorted(self.rows, reverse=True)]


def rank(vectors):
    """Rank of a family of vectors."""
    return Basis(vectors).rank


def in_span(vectors, v):
    """True iff v is a GF(2) combination of ``vectors``."""
    return Basis(vectors).contains(v)


def solve(vectors, target):
    """Mask m with XOR of {vectors[k] : bit k of m} == target, or None."""
    return Basis(vectors, track=True).express(target)


def span_size_log2(vectors):
    """log2 of the number of elements of the span."""
    return rank(vectors)


def kernel(vectors):
    """A basis of the relations among ``vectors``: masks m (over the family) with XOR == 0."""
    b = Basis(track=True)
    out = []
    for k, v in enumerate(vectors):
        before = b.count
        if not b.add(v):
            # v reduced to zero: the combination used, plus v itself, is a relation
            _, c = b._reduce(v, 1 << before)
            out.append(c)
    return out


def nullspace(rows, ncols):
    """A basis of ``{x : M x = 0}`` for the matrix whose rows are the ints ``rows`` (bit j of a
    row = column j, j < ncols); solutions are ints over ``ncols`` bits.

    ``gf2.kernel`` answers the other question (relations among a family of vectors).
    """
    # reduced row echelon form, pivot = lowest set bit for a readable back-substitution
    pivots = []           # (column, row)
    reduced = []
    for r in rows:
        for col, pr in pivots:
            if r >> col & 1:
                r ^= pr
        if r:
            col = (r & -r).bit_length() - 1
            # clear this column in the earlier rows so the form is fully reduced
            pivots = [(c, pr ^ r if pr >> col & 1 else pr) for c, pr in pivots]
            pivots.append((col, r))
    pivot_cols = {c for c, _ in pivots}
    out = []
    for free in range(ncols):
        if free in pivot_cols:
            continue
        x = 1 << free
        for col, pr in pivots:
            if pr >> free & 1:
                x |= 1 << col
        out.append(x)
    return out


def popcount(v):
    return v.bit_count()
