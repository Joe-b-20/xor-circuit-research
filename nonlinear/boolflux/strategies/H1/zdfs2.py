r"""Exhaustive search, case dim Z <= 2, for k-member GF(4)-norm last layers over a fixed E (agent H1).

Track C's member model (strategies/C: kj_search.Model, wsat.member_table): for a given gamma the
members are m = (z, zeta), z in F*, zeta in mu_5 (1275), the product N_{GF(4)}(Tr(Ax) + Tr_K(s v))
with v = n + gamma N, s = cube root of zeta, A = z / (zeta s). Z = span{z_m : m in S}.
C's zdfs.py covers dim Z = rank pi(S) (= 3, 4) and zdfs3.py dim Z = 3 with rank 4; C/NOTES lists
"dim Z = 2" as not covered. Here: for every 2-dim Z (10795) the members with z in Z \ 0 are
exactly 15; every subset S of them with |S| >= k is tested exactly (T in span(E + S)). dim Z = 1
gives only 5 members (< 8 needed). So this is complete for dim Z <= 2, any rank.
Prune (sound): if rank of pi over all 15 candidates > 15 - k + (k - 8) = 7, no subset works.

usage: python3 zdfs2.py --k 13 --gamma none|E --efile F --inv F
"""
import argparse
import itertools
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'C'))
import gf                                    # noqa: E402
import qmc                                   # noqa: E402
import wsat                                  # noqa: E402
from exp_stage3 import tables_of             # noqa: E402
from fam_check import gp                     # noqa: E402
from kj_search import Model                  # noqa: E402
from zdfs import MU5, CUBE_ROOT, subspaces   # noqa: E402


def rank(vs):
    return gf.Span(vs).dim()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--k', type=int, default=13)
    ap.add_argument('--gamma', default='none')
    ap.add_argument('--efile', required=True)
    ap.add_argument('--inv', required=True)
    a = ap.parse_args()
    t0 = time.time()
    M = Model(gp(int(a.gamma)) if a.gamma != 'none' else None, 'hard')
    l1, _ = tables_of(a.efile)
    _, inv = tables_of(a.inv)
    E = [gf.ONES] + gf.X + l1 + inv
    En = qmc.Normal(E)
    ET = qmc.Normal(E + M.T)
    Tn = [En.nf(t) for t in M.T]
    pi = {}; red = {}
    for z in range(1, 256):
        for zeta in MU5:
            s = CUBE_ROOT[zeta]
            Y = gf.mul(gf.INV[zeta], z); A = gf.mul(Y, gf.INV[s])
            tab = wsat.member_table(M, A, s)
            pi[(z, zeta)] = ET.nf(tab); red[(z, zeta)] = En.nf(tab)
    nZ = 0; pruned = 0; tested = 0; hits = []
    for Zb in subspaces(2):
        nZ += 1
        pts = [Zb[0], Zb[1], Zb[0] ^ Zb[1]]
        cands = [(z, zt) for z in pts for zt in MU5]
        if rank([pi[m] for m in cands]) > 7:
            pruned += 1; continue
        for size in range(a.k, 16):
            for S in itertools.combinations(cands, size):
                tested += 1
                sp = gf.Span([red[m] for m in S])
                if all(sp.contains(t) for t in Tn):
                    hits.append({'Z': Zb, 'S': S})
                    print(json.dumps({'event': 'HIT', 'Z': Zb, 'S': S}), flush=True)
    print(json.dumps({'event': 'done', 'k': a.k, 'gamma': a.gamma, 'efile': Path(a.efile).name,
                      'inv': Path(a.inv).name, 'dimE': En.dim(), 'Zs': nZ, 'pruned': pruned,
                      'subsets_tested': tested, 'hits': len(hits),
                      'secs': round(time.time() - t0, 1)}), flush=True)


if __name__ == '__main__':
    main()
