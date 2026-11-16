"""Own-depth polish: shrink a new record point to the fewest gates its own depth allows.

Role in the method (DESIGN.md section 4.5).  A chain searches at ``objective.search_cap`` and
records new nondominated points at their own depth, which can be below that cap (frontier
points, and worker bests when the soft slack is on or the search is uncapped).  The chain's free
removals are judged at the search cap, where dropping a helper usually deepens the circuit
instead of being free, so nothing minimised such a point at its own depth.  2026-10-30 witness
study: 5 of the 32 kept circuits (fox_mu8 601@7, 540@8, 1080@5; InvMixColumns 118@6, 170@5),
all recorded below their chain's search cap, lost 1-2 gates to plain removals at their own
depth; MixColumns 97@3, 89@4 and 88@5 did not shrink.

``polish(state, node_limit)`` takes a trimmed ``ValueSet`` built at the point's depth and finds
a largest set of helpers whose removal still realizes every target there.  Removable sets are
downward closed (fewer removals never hurt realizability), so a trimmed state shrinks only if
some single helper is removable; when none is (the common case) the cost is one ``strands``
screen per helper plus a trial removal for the few it passes.  Otherwise a depth-first branch
and bound over the removable helpers runs, exact unless ``node_limit`` stops it (the best set
found so far is kept).  Deterministic: candidates in ascending order, no RNG.
"""
from __future__ import annotations


class _Stop(Exception):
    pass


def _removable(state, cands, tset) -> list:
    """The values of ``cands`` whose single removal keeps every target realized."""
    out = []
    for v in cands:
        if state.strands(v, tset):
            continue
        u = state.remove((v,))
        ok = state.ok()
        state.restore(u)
        if ok:
            out.append(v)
    return out


def polish(state, node_limit: int = 20_000) -> tuple[list, bool, int]:
    """``(values to remove, exact, nodes)`` for a trimmed ``state`` (see the module
    docstring).  The state is left as it was; the list is empty when no helper can go."""
    tset, iset = state.tset, state.iset
    first = _removable(state, sorted(v for v in state.tri if v not in iset and v not in tset),
                       tset)
    if not first:
        return [], True, 0
    best: list = []
    path: list = []
    nodes = 0

    def search(cands):
        nonlocal best, nodes
        nodes += 1
        if nodes > node_limit:
            raise _Stop
        if len(path) + len(cands) <= len(best):
            return
        if not cands:
            best = list(path)
            return
        v = cands[0]
        u = state.remove((v,))
        path.append(v)
        try:
            search(_removable(state, cands[1:], tset))
        finally:
            path.pop()
            state.restore(u)
        search(cands[1:])

    try:
        search(first)
        exact = True
    except _Stop:
        exact = False
    return best or first[:1], exact, nodes
