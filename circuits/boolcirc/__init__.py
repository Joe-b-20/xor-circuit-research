"""boolcirc: Boolean circuits with XOR, XNOR, AND and NOT gates, read from NIST's circuit files.

The linear search (``search/linear/xorflux``) works on XOR-only circuits.  This package is the
library of ``circuits/check.py`` for Boolean circuits: it reads NIST's AES S-box circuits exactly as written (every gate
type keeps its own semantics), verifies them by complete truth tables, computes NIST's four
complexity metrics (#AND, AND depth, #Gates, gate depth) and extracts the *AND skeleton*: the
affine forms over inputs and AND outputs that every signal of the circuit is.  Standard library
only.  Neither search uses it.

Modules (import them by name; the function ``metrics.metrics`` and the module share a name):
``ncff`` (files), ``truth`` (truth tables, oracles, equivalence), ``metrics`` (NIST metrics and
file names), ``gf2`` (linear algebra over GF(2) on bit vectors), ``skeleton`` (the AND
skeleton and the linear sub-problem it defines).
"""
from . import gf2, metrics, ncff, skeleton, truth  # noqa: F401
from .ncff import Circuit, FormatError, Gate  # noqa: F401
from .truth import Function  # noqa: F401
