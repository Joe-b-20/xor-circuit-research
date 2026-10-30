"""Copied 64-bit v2 kernels used by ``moves/structural.py``.

The files are copies of the v2 kernels of an earlier version of the search (``search/engines/
vendor_v2/`` of the framework; v4's copy is in ``search/versions/v4-search-framework/engines/
vendor_v2/``). Each one starts with a header that gives
its origin, the SHA-256 of the source file and every change made here. They keep their own
wall-clock budgets (``max_seconds``), so moves built on them return ``deterministic=False``
proposals.

  v2_deadline_search.py    earliest_witness, deadline-aware reconstruct, optimize_depth3
  v2_structured_search.py  propose(kind='translate' | 'cores')
"""
