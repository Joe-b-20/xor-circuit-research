"""P4: stage 2 of the per-pair choice analysis (GD free unless GD given; inversion fixed at 13 XOR).

For choice c: linear >= top + pre + 13 + bottom with
  top    = nforms + H for the least feasible H (exhaustive helper sets, topenum_c),
  pre    >= 10 + rank X'(c), +1 unless some feasible top of that size has rank(Avail meet V) >= rank X'
           (a pre with exactly rank X' injections needs a basis of V in Avail),
  bottom exact from pairexact.py (else >= nt + 3 + n - 8).
H is raised only while the bound can still reach 57 (a 102).  Prints every c whose bound <= 57
(candidates for a 102) and a summary.

    python3 stage2.py CIRC PAIREXACT.jsonl GD > out.jsonl     (GD 99 = no deadline)
"""
import json
import sys

import topc


def main():
    path, pe, gd = sys.argv[1], sys.argv[2], int(sys.argv[3])
    recs = [json.loads(l) for l in open(pe) if l.startswith('{"c"')]
    n_checked = 0
    hits = []
    work = []
    for d in recs:
        b = d['bottom'] if d['bottom'] is not None else d['nt'] + 3 + d['n'] - 8
        if d['nforms'] + 10 + d['rankX'] + b <= 57:
            work.append((d['nforms'] + 10 + d['rankX'] + b, d))
    work.sort(key=lambda t: t[0])
    print(json.dumps(dict(work=len(work))), flush=True)
    for wi, (_, d) in enumerate(work):
        if wi % 200 == 0:
            print(json.dumps(dict(progress=wi, topc_calls=n_checked, hits=len(hits))), flush=True)
        b = d['bottom'] if d['bottom'] is not None else d['nt'] + 3 + d['n'] - 8
        nf, rk = d['nforms'], d['rankX']
        c = [int(ch) for ch in d['c']]
        bound = None
        for H in range(0, 4):
            if nf + H + 10 + rk + b > 57:
                break
            r = topc.run(path, gd, H, c)
            n_checked += 1
            if not r['sets']:
                continue
            if H:
                cov = max((x[2] or 0) for x in r['sets'])
            else:
                import pairscan, preinj
                _, _, _, pairs, X, P = pairscan.setup(path)
                forms, Xp = pairscan.choice(pairs, X, P, c)
                V = {0}
                for v in Xp:
                    if v not in V:
                        V |= {u ^ v for u in V}
                cov = preinj.rank([f for f in set(forms) | {1 << i for i in range(8)} if f in V])
            pre = 10 + rk + (0 if (cov is not None and cov >= rk) else 1)
            bound = nf + H + pre + b
            rec = dict(c=d['c'], top=nf + H, H=H, sets=len(r['sets']), cover=cov, rankX=rk, pre_lb=pre,
                       bottom=b, bound=bound, sample=r['sets'][:4])
            if bound <= 57:
                hits.append(rec)
            print(json.dumps(rec), flush=True)
            break
    print(json.dumps(dict(done=True, topc_calls=n_checked, candidates_102=len(hits))), flush=True)


if __name__ == '__main__':
    main()
