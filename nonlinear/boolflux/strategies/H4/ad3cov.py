"""Exact level-1 cover of V_N + U for the level-2 state of a zero-deficit record (U = the x-junk
its level 2 needs, free = M & X2), for l1 = 9, 10, ... (cover lemma; s <= 2).
usage: ad3cov.py JSONL INDEX [MAXL1]"""
import json
import sys
import time

import cover1
import cover_exact
import ad3mem as A
from ad3drop import state_vecs
from ad3sat import NT


def main():
    r = json.loads(open(sys.argv[1]).read().splitlines()[int(sys.argv[2])])
    mx = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    vecs = [cover1.reduce(v, A.E0) for v in state_vecs(r['state'], None)]
    inf, J = A.junk(vecs)
    assert inf == 0
    U = A.junk_space(vecs)
    VN = [A.to_wedge(t) for t in NT if t]
    Uw = [A.to_wedge(u) for u in U]
    Fw = [A.to_wedge(f) for f in A.m_cap_x2(vecs)]
    Fr = cover1.rowspace(Fw)
    d = len(cover1.rowspace([cover1.reduce(v, Fr) for v in VN + Uw]))
    print('J', J, 'dim(V_N+U)', len(cover1.rowspace(VN + Uw)), 'dim free', len(Fr), 'd', d, flush=True)
    import cover_s2
    for l1 in range(max(9, d), mx + 1):
        t0 = time.time()
        if l1 - d == 2:
            c, nt = cover_s2.cover2(VN + Uw, free=Fw); print('planes tested', nt)
        else:
            c = cover_exact.cover(VN + Uw, l1, free=Fw)
        print('l1', l1, 'cover', c is not None, 'secs %.1f' % (time.time() - t0), c, flush=True)
        if c is not None: break


if __name__ == '__main__':
    main()
