"""Generic <=8-support partition annealers, greedy (legacy) or joint (v2).

Only a scoped disjoint depth-three construction is searched. Arbitrary XOR
circuits, cancellations and outputs of greater support require other engines.
"""
from __future__ import annotations
from .common import validate_target


def propose(engine, target, rng, cfg, saved, stop, deadline):
    import time
    from .vendor_v2.deadline_search import _emit, optimize_depth3
    n, rows = validate_target(target)
    choices = dict(saved.get('partitions', {}))
    mutable = [m for m in dict.fromkeys(rows) if m.bit_count() > 2]
    if not choices:
        mutate = set(mutable)
    else:
        mutate = {rng.choice(mutable)} if mutable else set()
    recipes, parents = {}, set()
    for m in dict.fromkeys(rows):
        if stop():
            return None, {'operator': engine, 'stopped': True}
        bits = [1 << i for i in range(n) if m & (1 << i)]
        if len(bits) <= 1:
            continue
        if len(bits) == 2:
            recipes[m] = tuple(bits)
            continue
        key = str(m)
        if m in mutate or key not in choices:
            rng.shuffle(bits)
            size = rng.randint(max(1, len(bits)-4), min(4, len(bits)-1))
            a = sum(bits[:size]); choices[key] = [a, m ^ a]
        a, b = choices[key]
        recipes[m] = (a, b)
        parents.update((a, b))
    if engine.startswith('v2-'):
        result = optimize_depth3(parents, rng=rng,
                                max_seconds=min(cfg['proposal_seconds'], max(0.,deadline-time.monotonic())),
                                max_nodes=cfg['constructor_nodes'])
        if result is None:
            return None, {'operator': engine}
        # Required outputs can also be reused as parents. An actual cycle is
        # rejected by _emit; no algebraic cost estimate becomes a candidate.
        recipes.update(result['recipes'])
    else:
        # Legacy partition annealer: greedily share depth-one pairs; no exact
        # fixed-parent minimization or v2 deadline machinery is substituted.
        pairs = set()
        order = sorted(parents, key=lambda m: (-m.bit_count(), m))
        rng.shuffle(order)
        for parent in order:
            bits = [1 << i for i in range(n) if parent & (1 << i)]
            if len(bits) <= 1:
                continue
            if len(bits) == 2:
                recipes[parent] = tuple(bits); pairs.add(parent)
            elif len(bits) == 3:
                options = [(parent ^ bit, bit) for bit in bits]
                a,b = min(options, key=lambda p: (p[0] not in pairs, rng.random()))
                recipes[parent] = (a,b);pairs.add(a)
            else:
                a,b,c,d = bits
                options = [(a|b,c|d),(a|c,b|d),(a|d,b|c)]
                x,y = min(options,key=lambda p:(sum(m not in pairs for m in p),rng.random()))
                recipes[parent]=(x,y);pairs.update((x,y))
        for pair in pairs:
            recipes[pair] = tuple(1 << i for i in range(n) if pair & (1 << i))
    result = _emit(recipes, rows, [1 << i for i in range(n)], 3)
    if result is not None:
        # Caller copies this proposal state only if accepted.
        saved['partitions'] = choices
    return result, {'operator': engine, 'fixed_parent_optimum_is_not_global': True}
