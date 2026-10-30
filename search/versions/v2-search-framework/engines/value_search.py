"""New generic ports of legacy walk/LNS and v2 deadline/expansion mechanisms."""
from __future__ import annotations
import itertools
import math
import time
from .common import legacy_extract, validate_target


def propose(kind, current, target, cap, rng, cfg, saved, stop, deadline):
    n, rows = validate_target(target)
    inputs = [1 << i for i in range(n)]
    values = sorted(current['masks'])
    helpers = sorted(set(values) - set(rows))
    stats = {'operator': kind, 'victims': 0, 'injected': 0}
    if not helpers or stop():
        return None, stats
    walk = kind.endswith('walk')
    upgraded = kind.startswith('v2-')
    if walk:
        count = min(len(helpers), 1 if rng.random() < .6 else 2)
    else:
        count = min(len(helpers), rng.randint(1, cfg['destroy_max']))
    # A cone destroys correlated helpers; uniform deletion remains available.
    if not walk and rng.random() < cfg['cone_probability']:
        root = rng.choice(values)
        ancestors, stack = set(), [root]
        while stack:
            m = stack.pop()
            if m in ancestors:
                continue
            ancestors.add(m)
            stack.extend(current['recipes'].get(m, ()))
        local = sorted(set(helpers) & ancestors)
        victims = rng.sample(local, min(count, len(local))) if local else rng.sample(helpers, count)
    else:
        victims = rng.sample(helpers, count)
    stats['victims'] = len(victims)
    kept = set(values) - set(victims)
    vocabulary = sorted(kept | set(inputs))
    pool = list(saved.get('pool', ()))
    additions = set()
    samples = cfg['repair_candidates'] if walk else cfg['injection_samples']
    for _ in range(samples):
        if stop():
            break
        a, b = rng.sample(vocabulary, 2)
        m = a ^ b
        if m and m not in inputs and m not in victims:
            additions.add(m)
        if pool and not walk and rng.random() < cfg['pool_probability']:
            additions.add(rng.choice(pool))
    # Walk tests literal remove-one and remove-two/add-one neighborhoods.
    # Upgraded expansion also tries remove-one/add-two repairs.
    if walk:
        menus = [set()]
        menus.extend({m} for m in sorted(additions))
        if upgraded:
            pairs = list(itertools.combinations(sorted(additions), 2))
            rng.shuffle(pairs)
            menus.extend(set(p) for p in pairs[:cfg['expansion_candidates']])
    else:
        # Penalized victims let the rebuild keep necessary old structure.
        menus = [additions | set(victims)]
    best = None
    for extra in menus:
        if stop():
            break
        bank = kept | extra
        if len(bank) > cfg['bank_limit']:
            bank = kept | set(sorted(extra)[:max(0, cfg['bank_limit'] - len(kept))])
        stats['injected'] = max(stats['injected'], len(extra))
        preferred = {m: (cfg['victim_cost'] if m in victims else 1 if m in kept else 2) for m in bank}
        if upgraded:
            from .vendor_v2.deadline_search import reconstruct
            result = reconstruct(bank, rows, inputs=inputs, cap=cap, rng=rng,
                                 preferred=preferred,
                                 max_seconds=min(cfg['proposal_seconds'], max(0., deadline-time.monotonic())),
                                 beam_width=cfg['beam_width'], max_states=cfg['deadline_states'])
        else:
            result = legacy_extract(bank, target, cap, rng, preferred, stop)
        if result is not None and (best is None or (len(result['gates']), result['depth']) < (len(best['gates']), best['depth'])):
            best = result
        if walk and best is not None and len(best['gates']) < len(current['gates']):
            break
    saved['pool'] = sorted(set(pool) | set(values) | additions)[-cfg['pool_limit']:]
    return best, stats
