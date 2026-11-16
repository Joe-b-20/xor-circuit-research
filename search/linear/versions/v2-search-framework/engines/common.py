"""Dimension-safe replay and bounded value-bank operations for new adapters."""
from __future__ import annotations
import math
import time


def validate_target(target):
    n = target.get('input_count')
    rows = target.get('rows')
    if type(n) is not int or not 1 <= n <= 32:
        raise ValueError('input_count must be between 1 and 32')
    if not isinstance(rows, (list, tuple)) or not rows:
        raise ValueError('rows must be a nonempty ordered sequence')
    if type(target.get('output_count')) is not int or target['output_count'] != len(rows):
        raise ValueError('output_count must match rows')
    if any(type(m) is not int or not 0 < m < (1 << n) for m in rows):
        raise ValueError('rows must be nonzero masks in the input width')
    if not isinstance(target.get('id'), str) or not target['id']:
        raise ValueError('target id is required')
    return n, list(rows)


def replay(gates, target, cap=None):
    """Replay chronological pairs, coalesce duplicate values, prune dead gates."""
    from .vendor_v2.deadline_search import _emit
    n, rows = validate_target(target)
    if cap is not None and (type(cap) is not int or cap < 0):
        raise ValueError('depth_cap must be nonnegative or None')
    masks = [1 << i for i in range(n)]
    recipes = {}
    seen = set(masks)
    for pair in gates:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError('each gate must have two operands')
        if any(type(i) is not int or i < 0 or i >= len(masks) for i in pair):
            raise ValueError('gate must reference earlier signals')
        a, b = (masks[i] for i in pair)
        m = a ^ b
        if not m:
            raise ValueError('zero-valued gates are outside this engine model')
        if m not in seen:
            recipes[m] = (a, b)
            seen.add(m)
        masks.append(m)
    result = _emit(recipes, rows, [1 << i for i in range(n)], cap)
    if result is None:
        raise ValueError('circuit misses outputs or exceeds depth_cap')
    return result


def metric(witness):
    return len(witness['gates']), witness['depth']


def tuple_tree(value):
    return tuple(tuple_tree(v) for v in value) if isinstance(value, list) else value


def legacy_extract(bank, target, cap, rng, preferred, stop):
    """Historical fastest-arrival extraction, randomized sharing-aware pricing.

    This dimension-safe port retains the original earliest-depth restriction;
    v2 deadline reconstruction is intentionally a separate algorithm.
    """
    from .vendor_v2.deadline_search import _emit
    n, rows = validate_target(target)
    inputs = [1 << i for i in range(n)]
    bank = sorted(set(bank) | set(rows) | set(inputs))
    available = set(bank)
    levels = {m: 0 for m in inputs}
    changed = True
    checks = 0
    while changed:
        changed = False
        for m in bank:
            if m in inputs:
                continue
            best = levels.get(m, math.inf)
            for a in bank:
                checks += 1
                if checks % 128 == 0 and stop():
                    return None
                b = a ^ m
                if a >= b or b not in available or a not in levels or b not in levels:
                    continue
                d = 1 + max(levels[a], levels[b])
                if d < best:
                    best = d
            if best < levels.get(m, math.inf):
                levels[m] = best
                changed = True
        if stop():
            return None
    if any(m not in levels or (cap is not None and levels[m] > cap) for m in rows):
        return None
    recipes = {}
    demanded = set(rows) - set(inputs)
    pending = sorted(demanded, key=lambda m: levels[m], reverse=True)
    while pending:
        if stop():
            return None
        m = pending.pop(0)
        if m in recipes:
            continue
        options = []
        for a in bank:
            b = a ^ m
            if a >= b or b not in levels or a not in levels:
                continue
            if max(levels[a], levels[b]) >= levels[m]:
                continue
            cost = sum(0 if p in demanded or p in inputs else preferred.get(p, 1) for p in (a, b))
            options.append((cost + rng.random() * .7, a, b))
        if not options:
            return None
        _, a, b = min(options)
        recipes[m] = (a, b)
        for p in (a, b):
            if p not in inputs and p not in demanded:
                demanded.add(p)
                pending.append(p)
    return _emit(recipes, rows, inputs, cap)


def clock_stop(deadline, callback):
    return lambda: time.monotonic() >= deadline or bool(callback and callback())
