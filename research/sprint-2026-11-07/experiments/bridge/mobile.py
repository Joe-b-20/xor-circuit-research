#!/usr/bin/env python3
"""Hypothesis (b): are the weight-2 (input-pair) values of real 88 circuits 'mobile', i.e. removed by some
neutral remove1 move of the engine?  Uses the PES library (make_space('mc', None), fan).

usage: python3 mobile.py N   (first N sample records of bridge/profiles.json)
writes bridge/mobile.json
"""
import sys, json, time
sys.path.insert(0, '/home/joebachir20/xs-campaigns/2026-11-05-exit/pes')
from pes_lib import make_space, fan  # noqa: E402

OUT = '/home/joebachir20/xs-campaigns/2026-11-07-sprint/bridge'


def pc(v):
    return bin(v).count('1')


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    sp = make_space('mc', None)
    tset = sp.tset
    d = json.load(open(OUT + '/profiles.json'))
    recs = [r for r in d['results'] if r['tag'].startswith('sample:') and 'error' not in r][:n]
    out = []
    t0 = time.time()
    for r in recs:
        helpers = [v for v in r['values'] if v not in tset]
        S = frozenset(helpers)
        t1 = time.time()
        g, dep, neutral, downs, binds = fan(sp, S)
        w2 = {v for v in S if pc(v) == 2}
        removed = set()
        added = set()
        pure = 0      # neutral moves exchanging only weight-2 values
        for R, A, hk, dd in neutral:
            removed |= set(R)
            added |= set(A)
            if all(pc(v) == 2 for v in R) and all(pc(v) == 2 for v in A):
                pure += 1
        mobile_w2 = w2 & removed
        mobile_all = S & removed
        rec = dict(tag=r['tag'], engine_gates=g, depth=dep, n_neutral=len(neutral), n_down=len(downs), binds=binds,
                   n_helpers=len(S), n_w2=len(w2), n_w2_mobile=len(mobile_w2), n_mobile=len(mobile_all),
                   n_mobile_nonw2=len(mobile_all - w2), pure_w2_moves=pure,
                   added_w2=sum(1 for v in added if pc(v) == 2), added_total=len(added),
                   weight_hist_removed=sorted(__import__('collections').Counter(pc(v) for v in removed).items()),
                   weight_hist_helpers=sorted(__import__('collections').Counter(pc(v) for v in S).items()),
                   seconds=time.time() - t1)
        out.append(rec)
        print(json.dumps(rec), flush=True)
    json.dump(dict(records=out, seconds=time.time() - t0), open(OUT + '/mobile.json', 'w'))
    print('done', len(out), '%.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
