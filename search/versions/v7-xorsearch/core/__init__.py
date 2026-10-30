"""Core layer: the problem (Target), the incremental search state (ValueSet), circuits and
their independent verifier (Circuit, verify), the objective and work budgets.

Everything above this layer (moves, engine, campaign) builds on these names.
"""
from .budget import Budget
from .circuit import Circuit, Verdict, dag_sha256, matrix_sha256, ncff, normalise, parse_ncff, verify
from .objective import Objective
from .target import Seed, Target, catalog, generate, load_target
from .valueset import Journal, Undo, ValueSet, earliest_scan

__all__ = [
    'Budget', 'Circuit', 'Verdict', 'dag_sha256', 'matrix_sha256', 'ncff', 'normalise',
    'parse_ncff', 'verify', 'Objective', 'Seed', 'Target', 'catalog', 'generate', 'load_target',
    'Journal', 'Undo', 'ValueSet', 'earliest_scan',
]
