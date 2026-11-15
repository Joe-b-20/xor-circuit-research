"""AND removal on a circuit by random mc1 windows (R1).  remove_ands(c, rng, seconds) -> best circuit found
(fewest ANDs, then lexicographic), repeating until no window removes an AND or time is up."""
import random, time
import wres as R
import mc1
from boolflux.hub.common import metrics


def remove_ands(c, rng, seconds, K=10, maxg=16, maxo=6, amax=4, tries_per_round=400):
    t_end = time.time() + seconds
    cur = c; ref = c.output_tables(); log = []
    while time.time() < t_end:
        net = R.Net(cur); improved = False; seen = set()
        if len(net.ands) < 2: break
        for _ in range(tries_per_round):
            if time.time() > t_end: break
            W = mc1.windows(net, rng, K, maxg, maxo, amax)
            if not W: continue
            fw = frozenset(W)
            if fw in seen: continue
            seen.add(fw)
            rr = mc1.check_window(net, W, K)
            if rr is None: continue
            det, ctx, prods = rr
            if prods is None: continue
            rb = mc1.rebuild(net, ctx, prods)
            if rb is None: continue
            nc = R.splice(cur, net, W, ctx[0], ctx[1], *rb)
            mc = R.merge_dups(nc)
            if metrics(mc) <= metrics(nc): nc = mc
            if nc.output_tables() != ref: continue
            if metrics(nc)[0] < metrics(cur)[0]:
                log.append({'from': list(metrics(cur)), 'to': list(metrics(nc)), 'k': det['k'], 'g': det['g'], 'a': det['a']})
                cur = nc; improved = True; break
        if not improved: break
    return cur, log
